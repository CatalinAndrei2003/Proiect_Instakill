"""Week 5 time-split evaluation. Evaluation libraries are optional."""
import argparse, csv, hashlib, math, os, random, shutil, sqlite3, subprocess, tempfile, base64, io
from datetime import datetime, timezone
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.feed.service import FeedService
from app.repositories.social_repository import SocialRepository
from app.db.database import init_db

STRATEGIES=('chronological','popularity','for_you','learned')
def ndcg_at_10(ranking,relevant,k=10):
    if not relevant: return 0.0
    dcg=sum((1/math.log2(i+2)) for i,p in enumerate(ranking[:k]) if int(p) in relevant)
    ideal=sum(1/math.log2(i+2) for i in range(min(k,len(relevant))))
    return dcg/ideal if ideal else 0.0

def cutoff_default(db):
    c=sqlite3.connect(db); rows=[r[0] for r in c.execute('SELECT created_at FROM "like" ORDER BY created_at')]; c.close()
    if not rows: return '1970-01-01T00:00:00Z'
    return rows[max(0,math.ceil(.8*len(rows))-1)]

def create_snapshot(source,dest,cutoff):
    shutil.copy2(source,dest)
    c=sqlite3.connect(dest)
    c.execute('DELETE FROM "like" WHERE created_at >= ?',(cutoff,))
    # A pre-cutoff like cannot survive if its target post was not yet published.
    c.execute('DELETE FROM "like" WHERE post_id IN (SELECT id FROM post WHERE created_at >= ?)',(cutoff,))
    c.execute('DELETE FROM follow WHERE created_at >= ?',(cutoff,))
    c.execute('DELETE FROM post WHERE created_at >= ?',(cutoff,))
    c.commit(); c.close()

def activity_group(n):
    if n<10:return 'new'
    if n<50:return 'casual'
    if n<200:return 'regular'
    return 'power'

def bootstrap(values,seed,iterations=2000):
    if not values:return (0.0,0.0,0.0)
    rng=random.Random(seed); means=[]; n=len(values)
    for _ in range(iterations): means.append(sum(values[rng.randrange(n)] for _ in range(n))/n)
    means.sort(); return (sum(values)/n,means[int(.025*iterations)],means[min(iterations-1,int(.975*iterations))])

def evaluate(db,cutoff,seed,out,model_trained_through=None):
    out=Path(out); out.mkdir(parents=True,exist_ok=True)
    tmp=tempfile.NamedTemporaryFile(suffix='.db',delete=False); tmp.close(); snapshot=tmp.name
    create_snapshot(db,snapshot,cutoff)
    conn=sqlite3.connect(snapshot); conn.row_factory=sqlite3.Row
    pre={r['user_id']:r['n'] for r in conn.execute('SELECT user_id,COUNT(*) n FROM "like" WHERE created_at < ? GROUP BY user_id',(cutoff,))}
    snapshot_post_ids={r[0] for r in conn.execute('SELECT id FROM post')}
    # Relevance comes from the original database, not the time-truncated snapshot.
    source=sqlite3.connect(db); source.row_factory=sqlite3.Row
    later={}; evaluation_like_rows=[]
    for r in source.execute('SELECT user_id,post_id,created_at FROM "like" WHERE created_at >= ?',(cutoff,)):
        if int(r['post_id']) in snapshot_post_ids:
            later.setdefault(int(r['user_id']),set()).add(int(r['post_id']))
            evaluation_like_rows.append(dict(r))
    source.close()
    overlap_count=(sum(1 for r in evaluation_like_rows if r['created_at'] <= model_trained_through)
                   if model_trained_through else None)
    valid={u:rel for u,rel in later.items() if pre.get(u,0)>=3 and rel}
    service=FeedService(SocialRepository(snapshot)); rows=[]; scores={s:[] for s in STRATEGIES}; groups={}
    posts=[dict(r) for r in conn.execute('SELECT p.id post_id,p.user_id,p.content,p.created_at,COUNT(l.user_id) likes FROM post p LEFT JOIN "like" l ON l.post_id=p.id GROUP BY p.id')]
    for uid,relevant in sorted(valid.items()):
        group=activity_group(pre.get(uid,0)); groups[uid]=group
        for strategy in STRATEGIES:
            if strategy=='popularity':
                follows,liked,liked_authors,all_posts=service.repo.feed_data(uid)
                cand=[p for p in all_posts if int(p['user_id'])!=uid and int(p['post_id']) not in liked]
                if follows:cand=[p for p in cand if int(p['user_id']) in follows]
                ranking=[p['post_id'] for p in sorted(cand,key=lambda p:(-int(p.get('likes',0)),int(p['post_id'])))[:10]]
            else:
                result=service.get_feed(uid,10,strategy,datetime.fromisoformat(cutoff.replace('Z','+00:00')))
                ranking=[p['post_id'] for p in result['results']]
            score=ndcg_at_10(ranking,relevant); scores[strategy].append(score)
            rows.append([uid,strategy,f'{score:.10f}',len(relevant),group])
    conn.close(); os.unlink(snapshot)
    with open(out/'eval_results.csv','w',newline='',encoding='utf-8') as f:
        w=csv.writer(f,lineterminator='\n'); w.writerow(['user_id','strategy','ndcg_at_10','n_relevant','user_group']); w.writerows(rows)
    # paired bootstrap intervals for per-strategy mean and learned-best-baseline delta
    overlap_text=str(overlap_count) if overlap_count is not None else 'unknown (provide --model-trained-through)'
    table=['# Baseline comparison','', '**Demo seed data only — not official MovieLens results; learned uses fallback weights unless the lab model is supplied.**','',f'- Cut-off: `{cutoff}`',f'- Seed: `{seed}`',f'- Users: `{len(valid)}`',f'- Evaluation likes on snapshot posts: `{len(evaluation_like_rows)}`',f'- Evaluation likes within model training period: `{overlap_text}`',f'- DB SHA256: `{hashlib.sha256(Path(db).read_bytes()).hexdigest()}`',f'- Git commit: `{git_commit()}`','', '| Strategy | Mean NDCG@10 | 95% bootstrap interval | Users |','|---|---:|---:|---:|']
    means={}
    for i,s in enumerate(STRATEGIES):
        mean,lo,hi=bootstrap(scores[s],seed+i); means[s]=mean
        table.append(f'| {s} | {mean:.4f} | [{lo:.4f}, {hi:.4f}] | {len(scores[s])} |')
    baseline=max(means[x] for x in ('chronological','popularity','for_you'))
    best=max(('chronological','popularity','for_you'),key=lambda x:means[x])
    delta=[a-b for a,b in zip(scores['learned'],scores[best])]
    dm,dl,dh=bootstrap(delta,seed+20); verdict='wins' if dl>0 else ('loses' if dh<0 else 'unclear')
    table += ['',f'Learned minus best baseline ({best}): {dm:.4f}, 95% CI [{dl:.4f}, {dh:.4f}] — **{verdict}**','']
    table += ['## Activity slices','']
    for group in ('new','casual','regular','power'):
        users=[u for u,g in groups.items() if g==group]
        if not users: table.append(f'- {group}: no qualifying users'); continue
        # values are aligned in rows order; collect per user mapping from csv rows
        per={s:{} for s in STRATEGIES}
        for row in rows:
            if row[4]==group: per[row[1]][int(row[0])]=float(row[2])
        bl=max(('chronological','popularity','for_you'),key=lambda s:sum(per[s].values())/max(1,len(per[s])))
        d=[per['learned'][u]-per[bl][u] for u in users if u in per['learned'] and u in per[bl]]
        m,l,h=bootstrap(d,seed+100+len(group)); v='wins' if l>0 else ('loses' if h<0 else 'unclear')
        table.append(f'- {group} (n={len(d)}): learned − {bl} = {m:.4f}, 95% CI [{l:.4f}, {h:.4f}] — {v}')
    (out/'baseline_table.md').write_text('\n'.join(table)+'\n',encoding='utf-8')
    make_dashboard(out,table,scores,seed,rows)

def git_commit():
    try:return subprocess.check_output(['git','rev-parse','--short','HEAD'],stderr=subprocess.DEVNULL).decode().strip()
    except Exception:return 'unavailable'

def make_dashboard(out,table,scores,seed,rows):
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        (out/'dashboard.html').write_text('<html><body><h1>InstaKill evaluation</h1><p>Install optional eval dependencies to generate charts.</p></body></html>',encoding='utf-8'); return
    charts=[]
    # Strategy means + bootstrap intervals
    fig,ax=plt.subplots(); names=list(STRATEGIES); vals=[]; lows=[]; highs=[]
    for i,s in enumerate(names):
        m,l,h=bootstrap(scores[s],seed+i); vals.append(m); lows.append(m-l); highs.append(h-m)
    ax.bar(names,vals,yerr=[lows,highs],capsize=4); ax.set_ylim(0,1); ax.set_ylabel('NDCG@10'); ax.set_title('Which feed strategy ranks later likes best?'); charts.append(fig)
    # Signed learned-minus-best-baseline intervals by activity slice.
    baseline=max(('chronological','popularity','for_you'),key=lambda s:sum(scores[s])/max(1,len(scores[s])))
    by_user={s:{} for s in STRATEGIES}
    groups={}
    for row in rows:
        uid=int(row[0]); by_user[row[1]][uid]=float(row[2]); groups[uid]=row[4]
    slice_names=[]; deltas=[]; err_low=[]; err_high=[]
    for g in ('new','casual','regular','power'):
        us=[u for u,group in groups.items() if group==g and u in by_user['learned'] and u in by_user[baseline]]
        if not us: continue
        d=[by_user['learned'][u]-by_user[baseline][u] for u in us]; m,l,h=bootstrap(d,seed+30+len(g))
        slice_names.append(g); deltas.append(m); err_low.append(m-l); err_high.append(h-m)
    fig,ax=plt.subplots()
    if deltas:
        from matplotlib.colors import TwoSlopeNorm
        lo=min(min(deltas),-1e-6); hi=max(max(deltas),1e-6); norm=TwoSlopeNorm(vmin=lo,vcenter=0,vmax=hi)
        cmap=plt.get_cmap('coolwarm'); colors=[cmap(norm(v)) for v in deltas]
        ax.bar(slice_names,deltas,yerr=[err_low,err_high],capsize=4,color=colors)
    ax.axhline(0,linewidth=1); ax.set_ylabel('NDCG@10 difference'); ax.set_title('Does learned beat the best baseline in each user slice?'); charts.append(fig)
    # User score distribution
    fig,ax=plt.subplots(); ax.boxplot([scores[s] for s in names],tick_labels=names); ax.set_ylabel('NDCG@10'); ax.set_title('How variable are scores across users?'); charts.append(fig)
    for fig in charts:
        buf=io.BytesIO(); fig.savefig(buf,format='png',bbox_inches='tight'); plt.close(fig); charts[charts.index(fig)]=base64.b64encode(buf.getvalue()).decode()
    html='<!doctype html><html><head><meta charset="utf-8"><title>InstaKill Evaluation</title><style>body{font:16px system-ui;max-width:1100px;margin:2rem auto;padding:0 1rem}img{max-width:100%;height:auto}pre{white-space:pre-wrap}</style></head><body><h1>InstaKill evaluation dashboard</h1><pre>'+ '\n'.join(table)+'</pre>'
    for i,img in enumerate(charts,1): html+=f'<h2>Chart {i}</h2><img alt="evaluation chart" src="data:image/png;base64,{img}">'
    html+='</body></html>'; (out/'dashboard.html').write_text(html,encoding='utf-8')

def main():
    p=argparse.ArgumentParser(); p.add_argument('--db',default='instakill.db'); p.add_argument('--cutoff'); p.add_argument('--seed',type=int,default=42); p.add_argument('--out',default='reports/'); p.add_argument('--model-trained-through',help='ISO timestamp of the trained model data cutoff, for leakage count'); a=p.parse_args()
    cutoff=a.cutoff or cutoff_default(a.db); evaluate(a.db,cutoff,a.seed,a.out,a.model_trained_through)
if __name__=='__main__': main()
