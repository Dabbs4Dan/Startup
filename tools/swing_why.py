#!/usr/bin/env python3
"""Why are big crowd rises wrong? (Q008) Profiles the big-swing moments in the two daily markets.

Reads research/engine_room/swing_cohort.csv (run tools/swing_cohort.py first), the master and inputs_daily.
One row = one moment (event x time slot) with at least one busy line moving 15+ points. For each: how far the crowd's
center moved, how far the truth ended from where the crowd started, and what was already known that morning.
NOTE inputs_daily is lagged one day (as-of-safe): the futures change read on the snapshot date is the PREVIOUS trading
day's close-to-close move, known before the market opens. Prints tables only. Usage: python3 tools/swing_why.py
"""
import pathlib
import pandas as pd, numpy as np
pd.set_option('display.width',250)
R=str(pathlib.Path(__file__).resolve().parents[1])+'/'
C=pd.read_csv(R+'research/engine_room/swing_cohort.csv')
m=pd.read_csv(R+'data/lake/master/backtest_master.csv.gz',low_memory=False,usecols=['fuel','horizon','event','snapshot','snapshot_et','snapshot_date','crowd_center','settle_value','aaa_known_filled','aaa_chg_1d_c','aaa_chg_3d_c','fut_main_chg_1d_c','fut_main_chg_3d_c','weekday','trend_10d','streak_days','retail_minus_fut_vs_60d'])
m['market']=m.fuel+' '+m.horizon
i=pd.read_csv(R+'data/lake/master/inputs_daily.csv',usecols=['date','fut_ho','fut_rbob']).sort_values('date')
i['rbob_day']=i.fut_rbob.diff()*100; i['ho_day']=i.fut_ho.diff()*100
# event-transition level
m=m.sort_values(['event','snapshot_et']); m['c_before']=m.groupby('event').crowd_center.shift(1); m['prev_slot']=m.groupby('event').snapshot.shift(1)
C['dir']=np.where(C.up,'rise','drop')
E_=C.groupby(['market','event','snapshot_et','dir']).agg(lines=('move','size'),avg_move=('move','mean'),with_edge=('with_edge','mean'),fade_edge=('fade_edge','mean')).reset_index()
E_=E_.merge(m,on=['market','event','snapshot_et'],how='left').merge(i[['date','rbob_day','ho_day']],left_on='snapshot_date',right_on='date',how='left')
E_['fut_same_day']=np.where(E_.fuel=='gas',E_.rbob_day,E_.ho_day)
E_['crowd_move']=(E_.crowd_center-E_.c_before)*100
E_['truth_move']=(E_.settle_value-E_.c_before)*100
E_['left_over']=(E_.crowd_center-E_.settle_value)*100   # + = crowd ended too high
E_['aaa_tomorrow']=(E_.settle_value-E_.aaa_known_filled)*100
D=E_[E_.market.isin(['gas daily','diesel daily'])]
def summ(x):
    return pd.Series({'transitions':len(x),'events':x.event.nunique(),'crowd_move_c':x.crowd_move.mean(),'truth_move_c':x.truth_move.mean(),'justified_pct':100*x.truth_move.sum()/x.crowd_move.sum() if x.crowd_move.sum()!=0 else np.nan,
      'ended_too_high_pct':(x.left_over>0).mean()*100,'left_over_c':x.left_over.mean(),'aaa_today_chg':x.aaa_chg_1d_c.mean(),'aaa_today_up_pct':(x.aaa_chg_1d_c>0).mean()*100,
      'fut_same_day_c':x.fut_same_day.mean(),'fut_same_day_up_pct':(x.fut_same_day>0).mean()*100,'fut_prev_day_c':x.fut_main_chg_1d_c.mean(),'aaa_tomorrow_up_pct':(x.aaa_tomorrow>0).mean()*100,'with_edge':x.with_edge.mean()})
print(D.groupby(['market','dir']).apply(summ).round(2).T.to_string())
r=D[D.dir=='rise']
print('\nRISES split: same-day futures up vs down'); print(r.assign(k=np.where(r.fut_same_day>0,'futures rose the day before','futures did not rise the day before')).groupby(['market','k']).apply(summ)[['transitions','events','crowd_move_c','truth_move_c','justified_pct','ended_too_high_pct','with_edge']].round(1))
print('\nRISES split: AAA rose today vs fell today'); print(r.assign(k=np.where(r.aaa_chg_1d_c>0,'AAA rose today','AAA fell/flat today')).groupby(['market','k']).apply(summ)[['transitions','events','crowd_move_c','truth_move_c','justified_pct','ended_too_high_pct','with_edge']].round(1))
print('\nRISES split: trend'); print(r.groupby(['market','trend_10d']).apply(summ)[['transitions','events','crowd_move_c','truth_move_c','justified_pct','ended_too_high_pct','with_edge']].round(1))
print('\nRISES split: slot'); print(r.groupby(['market','snapshot']).apply(summ)[['transitions','events','crowd_move_c','truth_move_c','justified_pct','ended_too_high_pct','with_edge']].round(1))
print('\nRISES by weekday'); print(r.groupby(['market','weekday']).apply(summ)[['transitions','events','justified_pct','ended_too_high_pct','with_edge']].round(1))
print('\nRISES: streak (days AAA moving same way)'); print(r.assign(k=pd.cut(r.streak_days,[-99,-3,-1,0,2,99])).groupby(['market','k'],observed=True).apply(summ)[['transitions','events','justified_pct','ended_too_high_pct','with_edge']].round(1))
