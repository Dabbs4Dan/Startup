#!/usr/bin/env python3
"""Big-swing cohort: the largest slot-to-slot price moves on the busy lines, all six markets. A look-back (Q007).

A swing = the YES mid price of one line moving 15+ points between two neighboring time slots, with a spread of 10c or
less at both ends (so an empty book is not counted as a move). For each swing, two bets at the price AFTER the move:
  with  = buy the side that just gained (YES after an up move, NO after a down move), ask + taker fee
  fade  = buy the other side
The EVENT is the sample. Prints the pattern tables; writes research/engine_room/swing_cohort.csv (lab.swing_cohort).
First piece of the planned `paths` table (Track C). Usage: python3 tools/swing_cohort.py
"""
import pathlib
import pandas as pd, numpy as np
pd.set_option('display.width',250)
R=str(pathlib.Path(__file__).resolve().parents[1])+'/'
L=pd.read_csv(R+'data/lake/master/ladder_snapshots.csv.gz',low_memory=False)
s=pd.read_csv(R+'data/lake/master/slices.csv.gz',low_memory=False,usecols=['market','event','strike','snapshot','trend_10d','center'])
busy=s[['event','strike']].drop_duplicates().rename(columns={'strike':'floor_strike'})
e1=s.drop_duplicates('event').set_index('event')
L=L.merge(busy,on=['event','floor_strike']); L['market']=L.event.map(e1.market); L['trend']=L.event.map(e1.trend_10d)
L['t']=pd.to_datetime(L.snapshot_et); L['spread']=L.yes_ask-L.yes_bid; L['mid']=(L.yes_ask+L.yes_bid)/2
L=L.sort_values(['event','floor_strike','t']); g=L.groupby(['event','floor_strike'])
for c in ['mid','spread','snapshot','t']: L['p_'+c]=g[c].shift(1)
L['n_mid']=g['mid'].shift(-1)
T=L.dropna(subset=['p_mid']).copy()
T=T[(T.spread<=0.10)&(T.p_spread<=0.10)]
T['move']=(T.mid-T.p_mid)*100; T['hrs']=(T.t-T.p_t).dt.total_seconds()/3600
T['up']=T.move>0
fee=lambda p: 0.07*p*(1-p)
ya=T.yes_ask; na=1-T.yes_bid
T['with_cost']=np.where(T.up, ya+fee(ya), na+fee(na)); T['with_won']=np.where(T.up, T.settled_yes, 1-T.settled_yes)
T['fade_cost']=np.where(T.up, na+fee(na), ya+fee(ya)); T['fade_won']=1-T.with_won
T['with_edge']=(T.with_won-T.with_cost)*100; T['fade_edge']=(T.fade_won-T.fade_cost)*100
T['with_ret']=(T.with_won-T.with_cost)/T.with_cost*100; T['fade_ret']=(T.fade_won-T.fade_cost)/T.fade_cost*100
T['cont']=np.where(T.up,1,-1)*(T.n_mid-T.mid)*100
T['size']=pd.cut(T.move.abs(),[0,5,15,25,40,101],labels=['under 5','5-15','15-25','25-40','40+'],right=False)
T['when']=np.where(T.hrs>8,'overnight',T.p_snapshot+' to '+T.snapshot)
def ev(d,col):
    e=d.groupby('event')[col].mean(); n=len(e)
    return round(e.mean(),1), (round(2*e.std()/np.sqrt(n),1) if n>1 else np.nan), n
def table(d,by):
    rows=[]
    for k,x in d.groupby(by,observed=True):
        we,wn,n=ev(x,'with_edge'); fe,fn,_=ev(x,'fade_edge'); wr,_,_=ev(x,'with_ret'); fr,_,_=ev(x,'fade_ret')
        rows.append(dict(key=k if not isinstance(k,tuple) else ' | '.join(map(str,k)),swings=len(x),events=n,up_pct=round(x.up.mean()*100),with_price=round(x.with_cost.mean()*100,1),with_win=round(x.with_won.mean()*100,1),with_edge=we,noise=wn,fade_edge=fe,with_ret=wr,fade_ret=fr,next_move=round(x.cont.mean(),1)))
    return pd.DataFrame(rows)
if __name__=='__main__':
    print('ALL transitions by size, per market'); print(table(T,['market','size']).to_string(index=False))
    C=T[T.move.abs()>=15]
    C[['market','event','floor_strike','p_snapshot','snapshot','snapshot_et','hrs','p_mid','mid','move','up','spread','trend','with_cost','with_won','fade_cost','with_edge','fade_edge']].round(4).to_csv(R+'research/engine_room/swing_cohort.csv',index=False)
    print('\nCOHORT >=15: by market'); print(table(C,['market']).to_string(index=False))
    print('\nby market x direction'); print(table(C,['market','up']).to_string(index=False))
    D=C[C.market.isin(['gas daily','diesel daily'])]
    print('\ndaily: by when'); print(table(D,['market','when']).to_string(index=False))
    print('\ndaily: by trend x direction'); print(table(D,['market','trend','up']).to_string(index=False))
    C2=C.copy(); C2['end']=pd.cut(C2.with_cost,[0,.5,.7,.85,1.01],labels=['under 50','50-70','70-85','85+'])
    print('\nby where the price ended (price of the side that gained)'); print(table(C2[C2.market.isin(['gas daily','gas weekly','diesel daily'])],['market','end']).to_string(index=False))
