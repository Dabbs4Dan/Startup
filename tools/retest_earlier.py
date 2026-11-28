#!/usr/bin/env python3
"""Re-test of the earlier answers kept in the question log (the P rows), on the current master. Dan, 2026-11-28.

One block per kept question: P01 momentum, P04/P07 diesel favorites, P06 gas favorites, P22 crowd range, P17 evening
overshoot, P12 ceiling by time span, P13 limit orders, P15 bet size, P18/P19 depth and settle rule, P20 the open,
P09 pass-through, P11 edge needed, P14 truckstops, P08 state blend. The event is the sample; cost = ask + taker fee.
Prints tables only (results are written up in research/QUESTION_LOG.md). Usage: python3 tools/retest_earlier.py
"""
import pathlib
import pandas as pd, numpy as np, sqlite3, glob, json, sys
pd.set_option('display.width',260); pd.set_option('display.max_columns',40)
R=str(pathlib.Path(__file__).resolve().parents[1])+'/'
m=pd.read_csv(R+'data/lake/master/backtest_master.csv.gz',low_memory=False); m['market']=m.fuel+' '+m.horizon
m=m[m.answer_may_be_public==0]
s=pd.read_csv(R+'data/lake/master/slices.csv.gz',low_memory=False)
fee=lambda p:0.07*p*(1-p)
def evstat(d,col):
    e=d.groupby('event')[col].mean(); n=len(e); return round(e.mean(),1), round(2*e.std()/np.sqrt(n),1) if n>1 else np.nan, n
DM=['diesel daily','gas daily']
print('\n##### P01 momentum: slope of crowd expected change and of truth on yesterday AAA move (10 AM, then close)')
for mk in DM:
    for snap in ('10am','close'):
        d=m[(m.market==mk)&(m.snapshot==snap)].dropna(subset=['aaa_chg_1d_c','crowd_expected_change_c','change_to_settle_c'])
        x=d.aaa_chg_1d_c.values; sl=lambda y: round(float((x*y).sum()/(x*x).sum()),2)
        r2=lambda y: round(float(np.corrcoef(x,y)[0,1]**2),2)
        print(mk,snap,'days',len(d),'crowd slope',sl(d.crowd_expected_change_c.values),'r2',r2(d.crowd_expected_change_c.values),'| truth slope',sl(d.change_to_settle_c.values),'r2',r2(d.change_to_settle_c.values))
print('\n##### P04 + P07 diesel favorites at 10 AM')
s['fav_ask']=np.where(s.fav_side=='yes',s.yes_ask,s.no_ask); s['edge']=(s.fav_won-s.fav_cost)*100; s['ret']=(s.fav_won-s.fav_cost)/s.fav_cost*100
d=s[(s.market=='diesel daily')&(s.snapshot=='10am')]
for lo,hi,name in ((.75,.85,'75-85c'),(.60,.97,'60-97c')):
    x=d[d.fav_ask.between(lo,hi)]
    print(name,'ALL: edge,noise,days',evstat(x,'edge'),'win%',round(x.groupby('event').fav_won.mean().mean()*100,1),'ret per $100',evstat(x,'ret')[:2])
    x=x.assign(per=np.where(x.settle_date<='2026-09-17','Aug 3-Sep 17 (fast rise)','Sep 18 on'),mo=x.settle_date.str[:7])
    for k,g in x.groupby('per'): print('   ',k,evstat(g,'edge'),'win%',round(g.groupby('event').fav_won.mean().mean()*100,1),'ret',evstat(g,'ret')[:2])
    print('    by month ret:',{k:evstat(g,'ret')[0] for k,g in x.groupby('mo')})
    print('    by trend edge:',{k:evstat(g,'edge') for k,g in x.groupby('trend_10d')})
print('\n##### P06 gas favorites at 10 AM (60-97c) and gas YES at 83.5c or less')
for mk in ('gas daily','gas weekly'):
    d=s[(s.market==mk)&(s.snapshot=='10am')]
    x=d[d.fav_ask.between(.60,.97)]; print(mk,'favorites 60-97c: edge',evstat(x,'edge'),'ret',evstat(x,'ret')[:2])
    y=d[(d.fav_side=='yes')&(d.yes_ask<=.835)]; print(mk,'YES-favorite at 83.5c or less: edge',evstat(y,'edge'),'ret',evstat(y,'ret')[:2])
    z=s[(s.market==mk)&(s.fav_side=='yes')&(s.yes_ask<=.835)]; print(mk,'  same, all slots: edge',evstat(z,'edge'),'ret',evstat(z,'ret')[:2])
print('\n##### P22 crowd range: share of events where the answer lands inside center +/- width')
ev=s.drop_duplicates(['market','event','snapshot']).copy(); ev['inside']=((ev.settle_value-ev.center).abs()*100<=ev.width)
print(ev[ev.snapshot=='10am'].groupby('market').inside.agg(['mean','size']).round(3).T.to_string())
print('all slots:',ev.groupby('market').inside.mean().round(3).to_dict())
print('daily by slot:'); print(ev[ev.market.isin(DM)].pivot_table(index='market',columns='snapshot',values='inside')[['open','10am','noon','3pm','6pm','10pm','close']].round(2).to_string())
print('\n##### P17 evening overshoot after the strongest 5-day rises: buy NO at 10 PM, NO ask 25-97c')
mm=m[['event','snapshot','aaa_chg_5d_c']].drop_duplicates(['event','snapshot'])
x=s[(s.snapshot=='10pm')].merge(mm,on=['event','snapshot'])
x=x[x.no_ask.between(.25,.97)].copy(); x['no_cost']=x.no_ask+fee(x.no_ask); x['no_won']=1-x.settled_yes; x['nret']=(x.no_won-x.no_cost)/x.no_cost*100; x['nedge']=(x.no_won-x.no_cost)*100
for mk in DM:
    g=x[x.market==mk]; days=g.drop_duplicates('event'); q=days.aaa_chg_5d_c.quantile([.6,.8]).values
    for name,sel in (('top fifth of 5-day rises',g.aaa_chg_5d_c>=q[1]),('all other days',g.aaa_chg_5d_c<q[1]),('5-day change above 0',g.aaa_chg_5d_c>0),('5-day change 0 or below',g.aaa_chg_5d_c<=0)):
        h=g[sel]; print(mk,name,'(cut %.1fc)'%q[1] if 'fifth' in name else '','ret per $100,noise,days',evstat(h,'nret'),'edge pts',evstat(h,'nedge')[:2])
    h=g[g.aaa_chg_5d_c>=q[1]]; e=h.groupby('event').nret.mean(); half=len(e)//2; e=e.sort_index(); print('   top fifth: first half',round(e.iloc[:half].mean(),1),'second half',round(e.iloc[half:].mean(),1))
print('\n##### P12 ceiling: perfect foresight 10 AM -> 10 PM same day, exit at the bid (busy lines, spread 10c or less)')
L=pd.read_csv(R+'data/lake/master/ladder_snapshots.csv.gz',low_memory=False)
busy=s[['event','strike']].drop_duplicates().rename(columns={'strike':'floor_strike'}); L=L.merge(busy,on=['event','floor_strike'])
L['day']=L.snapshot_et.str[:10]; mkmap=s.drop_duplicates('event').set_index('event').market; L['market']=L.event.map(mkmap)
a=L[L.snapshot=='10am'][['market','event','floor_strike','day','yes_bid','yes_ask','settled_yes']]; b=L[L.snapshot=='10pm'][['event','floor_strike','day','yes_bid','yes_ask']]
j=a.merge(b,on=['event','floor_strike','day'],suffixes=('_am','_pm')); j=j[((j.yes_ask_am-j.yes_bid_am)<=.10)&((j.yes_ask_pm-j.yes_bid_pm)<=.10)]
cy=j.yes_ask_am+fee(j.yes_ask_am); cn=(1-j.yes_bid_am)+fee(1-j.yes_bid_am)
gy=(j.yes_bid_pm-fee(j.yes_bid_pm)-cy)/cy; gn=((1-j.yes_ask_pm)-fee(1-j.yes_ask_pm)-cn)/cn
j['ceil_bid']=np.maximum(np.maximum(gy,gn),0)*100
my=(j.yes_bid_am+j.yes_ask_am)/2; mp=(j.yes_bid_pm+j.yes_ask_pm)/2
j['ceil_mid']=np.maximum((mp-my)/my,((1-mp)-(1-my))/(1-my)).clip(lower=0)*100
hy=(j.settled_yes-cy)/cy; hn=((1-j.settled_yes)-cn)/cn; j['ceil_settle']=np.maximum(hy,hn)*100
j['group']=j.market.str.split().str[1]
print(j.groupby('group').apply(lambda g: pd.Series({'lines':len(g),'events':g.event.nunique(),'per$100 exit at 10PM bid':round(g.groupby('event').ceil_bid.mean().mean(),1),'per$100 mid to mid no costs':round(g.groupby('event').ceil_mid.mean().mean(),1),'per$100 hold to settle':round(g.groupby('event').ceil_settle.mean().mean(),1)})).to_string())
print(j.groupby('market').apply(lambda g: pd.Series({'events':g.event.nunique(),'bid':round(g.groupby('event').ceil_bid.mean().mean(),1),'mid':round(g.groupby('event').ceil_mid.mean().mean(),1)})).to_string())
print('\n##### P13 limit orders: makers who ended up holding the favorite side at 60-97c (trade tape, before fees)')
for db,fu in ((R+'data/kalshi_twins.db','diesel daily'),(R+'data/gas/kalshi_gas.db','gas daily')):
    con=sqlite3.connect(db); t=pd.read_sql("SELECT t.ticker,t.event_date,t.yes_price,t.no_price,t.count,t.taker_side,m.result FROM kalshi_trades t JOIN kalshi_markets m ON m.ticker=t.ticker WHERE m.result IN ('yes','no')",con)
    mside=np.where(t.taker_side=='yes','no','yes'); mp_=np.where(mside=='yes',t.yes_price,t.no_price); won=(mside==t.result).astype(float)
    t['cost']=t['count']*mp_; t['pnl']=t['count']*(won-mp_); t['mp']=mp_
    for lo,hi in ((.60,.97),(.03,.40)):
        f=t[(t.mp>=lo)&(t.mp<=hi)]; d=f.groupby('event_date')[['cost','pnl']].sum(); r=d.pnl/d.cost
        print(fu,'maker bought at %d-%dc:'%(lo*100,hi*100),'days',len(d),'ret per $100',round(100*d.pnl.sum()/d.cost.sum(),1),'noise',round(200*r.std()/np.sqrt(len(d)),1),'days positive %',round((d.pnl>0).mean()*100),'by month',{k:round(100*g.pnl.sum()/g.cost.sum(),1) for k,g in d.groupby(d.index.str[:7])})
    tp=np.where(t.taker_side=='yes',t.yes_price,t.no_price); tw=(t.taker_side==t.result).astype(float); t['tc']=t['count']*tp; t['tpnl']=t['count']*(tw-tp)
    f=t[(tp>=.60)&(tp<=.97)]; d=f.groupby('event_date')[['tc','tpnl']].sum(); print(fu,'TAKER bought favorite 60-97c: ret per $100',round(100*d.tpnl.sum()/d.tc.sum(),1),'days',len(d))
print('\n##### P15 bet size: dollars resting at the best price, favorite side (ask 60-97c)')
ob=pd.concat([pd.read_csv(f) for f in sorted(glob.glob(R+'data/live/kalshi_orderbook/*.csv'))],ignore_index=True)
print('series in book:',ob.event.str.split('-').str[0].value_counts().to_dict(),'days',ob.ts_et.str[:10].nunique(),ob.ts_et.min(),ob.ts_et.max())
best=ob.sort_values('price').groupby(['ts_utc','ticker','side']).tail(1); best=best.assign(ask=1-best.price); best['dollars']=best.contracts*best.ask
fav=best[best.ask.between(.60,.97)].copy(); fav['hr']=pd.to_datetime(fav.ts_et).dt.hour; fav['ser']=fav.event.str.split('-').str[0]
for name,g in (('all hours',fav),('10 AM to 6 PM',fav[fav.hr.between(10,17)]),('10 PM to midnight',fav[fav.hr>=22]),('8 to 10 AM',fav[fav.hr.between(8,9)])):
    for ser,h in g.groupby('ser'): print(ser,name,'quotes',len(h),'median $',round(h.dollars.median()),'$1K fits %',round((h.dollars>=1000).mean()*100),'$5K fits %',round((h.dollars>=5000).mean()*100),'$10K fits %',round((h.dollars>=10000).mean()*100))
print('\n##### P18/P19 data depth and settle rule'); print(m.groupby('market').agg(events=('event','nunique'),first=('settle_date','min'),last=('settle_date','max')).to_string())
print('events with busy ladders:',s.groupby('market').event.nunique().to_dict())
e1=m.drop_duplicates('event'); print('close hour (ET) counts by market:',e1.groupby('market').close_et.apply(lambda x: pd.to_datetime(x).dt.strftime('%H:%M').value_counts().head(2).to_dict()).to_dict())
print(open(R+'data/lake/master/SPINE.md').read().split('## Join checks')[1].split('## Sheet')[0][-420:])
print('\n##### P20 the open: crowd miss vs simple forecasts (median abs miss, cents), walk-forward on the last 40% of days')
for mk in DM:
    d=m[(m.market==mk)&(m.snapshot=='open')].dropna(subset=['aaa_chg_1d_c','change_to_settle_c','crowd_expected_change_c','fut_main_chg_1d_c']).sort_values('settle_date').reset_index(drop=True)
    d['wd']=pd.to_datetime(d.settle_date).dt.dayofweek; n=len(d); k=int(n*.6); te=d.iloc[k:]
    def fit(cols):
        X=np.column_stack([np.ones(k)]+[d[c].values[:k] for c in cols]); y=d.change_to_settle_c.values[:k]; b=np.linalg.lstsq(X,y,rcond=None)[0]
        Xt=np.column_stack([np.ones(n-k)]+[te[c].values for c in cols]); return round(float(np.median(np.abs(te.change_to_settle_c.values-Xt@b))),2)
    wd=pd.get_dummies(d.wd,prefix='wd',drop_first=True).astype(float); d=pd.concat([d,wd],axis=1); te=d.iloc[k:]
    print(mk,'test days',n-k,'| crowd',round(float((te.change_to_settle_c-te.crowd_expected_change_c).abs().median()),2),'| no change',round(float(te.change_to_settle_c.abs().median()),2),'| yesterday move',fit(['aaa_chg_1d_c']),'| + futures',fit(['aaa_chg_1d_c','fut_main_chg_1d_c','fut_main_chg_3d_c']),'| + weekday',fit(['aaa_chg_1d_c','fut_main_chg_1d_c','fut_main_chg_3d_c']+list(wd.columns)),'| + 5d,10d AAA',fit(['aaa_chg_1d_c','aaa_chg_3d_c','aaa_chg_5d_c','fut_main_chg_1d_c','fut_main_chg_3d_c','fut_main_chg_5d_c']+list(wd.columns)))
print('\n##### P09 pump prices trail futures: daily AAA change vs futures change k days earlier')
aaa=pd.read_csv(R+'data/lake/master/aaa_daily.csv'); 
for fu,ff in (('diesel','fut_ho_1d.csv'),('gas','fut_rbob_1d.csv')):
    a=aaa[aaa.fuel==fu].drop_duplicates('date').set_index('date').value; a.index=pd.to_datetime(a.index); a=a.asfreq('D'); da=a.diff()*100
    f=pd.read_csv(R+'data/lake/history/'+ff).drop_duplicates('date').set_index('date').close; f.index=pd.to_datetime(f.index); f=f.asfreq('D').ffill(); df=f.diff()*100
    z=pd.DataFrame({'da':da}); 
    for k_ in range(0,15): z[f'f{k_}']=df.shift(k_)
    z=z.dropna(); z=z[z.index>='2025-01-01']
    X=np.column_stack([np.ones(len(z))]+[z[f'f{k_}'].values for k_ in range(0,15)]); b=np.linalg.lstsq(X,z.da.values,rcond=None)[0][1:]
    cum=np.cumsum(b); print(fu,'days',len(z),'pass-through per 1c of futures, by lag day 0..14:',np.round(b,3).tolist()); print('   cumulative after 1,3,5,7,10,14 days:',[round(float(cum[i]),2) for i in (1,3,5,7,10,14)],'| share of 14-day total reached by day 3:',round(float(cum[3]/cum[14]),2),'day 7:',round(float(cum[7]/cum[14]),2))
print('\n##### P11 edge needed: bets to tell an edge from luck (2 standard errors), favorite at 80c that wins 85%')
p,c=.85,.80+fee(.80); sd=np.sqrt(p*(1-p))/c
for e in (.03,.05,.08,.10): print('edge %d%% per $: bets needed'%(e*100),round((2*sd/e)**2))
real=s[(s.market=='diesel daily')&(s.snapshot=='10am')&s.fav_ask.between(.6,.97)].groupby('event').ret.mean(); print('real day-to-day spread of a favorite bet (diesel 10 AM): sd %.0f per $100 -> bets for 8%%: %d, for 3%%: %d'%(real.std(),(2*real.std()/8)**2,(2*real.std()/3)**2))
print('\n##### P14 truckstops'); t=pd.read_csv(R+'research/engine_room/l3_truckstop_scorecard.csv'); print(t[['bet_day','settle_day','ts_move_c','aaa_change_c','surprise_10am_c','surprise_close_c','status']].to_string(index=False)); print('truckstop files:',len(glob.glob(R+'data/live/truckstops/*.csv')))
print('\n##### P08 state blend'); con=sqlite3.connect(R+'data/kalshi_twins.db'); print(pd.read_sql("select algo_id,window,n,median_abs_miss_c,share_within_tol,verdict from algo_scorecard where algo_id like 'L2%'",con).to_string(index=False))
