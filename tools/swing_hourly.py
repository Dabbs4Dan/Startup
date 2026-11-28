#!/usr/bin/env python3
"""Big swings vs HOURLY futures (Q009). Needs data/lake/history/yahoo_RB_60m_*.csv and yahoo_HO_60m_*.csv
(hourly bars since Jul 2024; landed 2026-11-28 after the user-agent fix in history_pull.py) and swing_cohort.csv.

For each big-swing moment in the two daily markets: the futures move in the same hours, the move so far that day
(since 5 PM the evening before) and the previous trading day's move (2 PM to 2 PM), all read without peeking
(price at time t = the open of the last hourly bar that started at or before t). Prints tables only.
Usage: python3 tools/swing_hourly.py
"""
import pandas as pd, numpy as np, glob, pathlib
pd.set_option('display.width',300); pd.set_option('display.max_columns',30)
R=str(pathlib.Path(__file__).resolve().parents[1])+'/'
def fut(sym):
    d=pd.concat([pd.read_csv(f) for f in sorted(glob.glob(R+f'data/lake/history/yahoo_{sym}_60m_*.csv'))]).drop_duplicates('ts_utc')
    d['t']=pd.to_datetime(d.ts_utc).dt.tz_convert('America/New_York').dt.tz_localize(None)
    return d.sort_values('t')[['t','open']].rename(columns={'open':'px'})
F={'gas':fut('RB'),'diesel':fut('HO')}
C=pd.read_csv(R+'research/engine_room/swing_cohort.csv')
m=pd.read_csv(R+'data/lake/master/backtest_master.csv.gz',low_memory=False,usecols=['fuel','horizon','event','snapshot','snapshot_et','crowd_center','settle_value','aaa_known_filled','trend_10d'])
m['market']=m.fuel+' '+m.horizon; m['t']=pd.to_datetime(m.snapshot_et)
m=m.sort_values(['event','t']); m['c_before']=m.groupby('event').crowd_center.shift(1); m['t_before']=m.groupby('event').t.shift(1)
C['dir']=np.where(C.up,'rise','drop')
E=C.groupby(['market','event','snapshot_et','dir']).agg(lines=('move','size'),with_edge=('with_edge','mean'),fade_edge=('fade_edge','mean')).reset_index()
E=E.merge(m,on=['market','event','snapshot_et']); E=E[E.market.isin(['gas daily','diesel daily'])].dropna(subset=['t_before'])
def px_at(fuel,ts):
    f=F[fuel]; return pd.merge_asof(pd.DataFrame({'t':ts}).sort_values('t'),f,on='t',tolerance=pd.Timedelta('5h')).set_index(ts.sort_values().index).px.reindex(ts.index)
out=[]
for fuel,g in E.groupby('fuel'):
    g=g.copy(); g['f_now']=px_at(fuel,g.t); g['f_before']=px_at(fuel,g.t_before)
    y=(g.t.dt.normalize()-pd.Timedelta(hours=7))   # 5 PM the evening before
    g['f_yday']=px_at(fuel,y)
    out.append(g)
E=pd.concat(out); E['fut_window_c']=(E.f_now-E.f_before)*100; E['fut_day_c']=(E.f_now-E.f_yday)*100
E['crowd_move']=(E.crowd_center-E.c_before)*100; E['truth_move']=(E.settle_value-E.c_before)*100; E['left_over']=(E.crowd_center-E.settle_value)*100
print('moments',len(E),'with futures window',E.fut_window_c.notna().sum(),'with day move',E.fut_day_c.notna().sum())
print(E.groupby(['market','dir'])[['fut_window_c','fut_day_c']].agg(['mean','median']).round(2))
def S(x):
    e=x.groupby('event').with_edge.mean(); f=x.groupby('event').fade_edge.mean(); n=len(e)
    return pd.Series({'moments':len(x),'days':n,'crowd_move_c':round(x.crowd_move.mean(),2),'truth_move_c':round(x.truth_move.mean(),2),'ended_too_high_pct':round((x.left_over>0).mean()*100),'with_edge':round(e.mean(),1),'noise':round(2*e.std()/np.sqrt(n),1) if n>1 else np.nan,'fade_edge':round(f.mean(),1)})
def lab(v,th): return np.where(v>th,'futures UP',np.where(v<-th,'futures DOWN','futures flat'))
for col,th,name in (('fut_window_c',0.3,'same window (between the two time slots)'),('fut_day_c',1.0,'so far that day (since 5 PM the evening before)')):
    D=E.dropna(subset=[col]).copy(); D['f']=lab(D[col],th)
    print('\n=== futures move',name,'threshold',th,'c ==='); print(D.groupby(['market','dir','f']).apply(S).to_string())
D=E.dropna(subset=['fut_day_c']).copy(); D['backed']=np.where(D.dir=='rise',D.fut_day_c>1.0,D.fut_day_c<-1.0)
print('\n=== backed by the day so far ==='); print(D.groupby(['market','dir','backed']).apply(S).to_string())
late=D[D.snapshot.isin(['10pm','close'])]; print('\nlate only'); print(late.groupby(['market','dir','backed']).apply(S).to_string())
def daily(sym):
    d=pd.concat([pd.read_csv(f) for f in sorted(glob.glob(R+f'data/lake/history/yahoo_{sym}_60m_*.csv'))]).drop_duplicates('ts_utc').reset_index(drop=True)
    d['t']=pd.to_datetime(d.ts_utc).dt.tz_convert('America/New_York').dt.tz_localize(None)
    x=d[d.t.dt.hour==14].copy(); x['day']=x.t.dt.normalize()
    return (x.groupby('day').open.last().diff()*100)
P={'gas':daily('RB'),'diesel':daily('HO')}
def prev_move(fuel,day):
    s=P[fuel]; s=s[s.index<day]; return s.iloc[-1] if len(s) else np.nan
E['prev_day_c']=[prev_move(f,t.normalize()) for f,t in zip(E.fuel,E.t)]
r=E[E.dir=='rise'].copy(); r['yday']=np.where(r.prev_day_c>0,'yesterday futures UP','yesterday not up')
print('\n=== rises by the previous trading day (2 PM to 2 PM) ==='); print(r.groupby(['market','yday']).apply(S).to_string())
r2=r.dropna(subset=['fut_day_c']).copy(); r2['today']=np.where(r2.fut_day_c>0,'today UP so far','today not up')
print('\n=== rises: yesterday x today so far ==='); print(r2.groupby(['market','yday','today']).apply(S).to_string())
d=E[E.dir=='drop'].copy(); d['yday']=np.where(d.prev_day_c<0,'yesterday futures DOWN','yesterday not down')
print('\n=== drops by the previous trading day ==='); print(d.groupby(['market','yday']).apply(S).to_string())
