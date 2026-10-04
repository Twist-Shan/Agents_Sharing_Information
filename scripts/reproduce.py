"""Run the archived numerical checks offline, in a disposable output copy."""
from pathlib import Path
import argparse,hashlib,json,os,shutil,subprocess,sys
ROOT=Path(__file__).resolve().parents[1]
def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output',type=Path,default=ROOT/'outputs/reproduction')
    a=p.parse_args();out=a.output.resolve();source=ROOT/'reproduction'
    if out==source.resolve() or source.resolve() in out.parents:
        raise ValueError('Output must not modify the archived package')
    if out.exists():raise FileExistsError('Choose a new output directory: '+str(out))
    hashes=json.loads((source/'PACKAGE_SHA256.json').read_text())
    for name,digest in hashes.items():
        assert hashlib.sha256((source/name).read_bytes()).hexdigest()==digest,name
    out.mkdir(parents=True);work=out/'work';shutil.copytree(source,work)
    blocker=out/'network_block';blocker.mkdir()
    (blocker/'sitecustomize.py').write_text("import sys\ndef block(event,args):\n    if event in ('socket.connect','socket.getaddrinfo'):raise RuntimeError('Offline reproduction forbids network')\nsys.addaudithook(block)\n")
    env=dict(os.environ);env['PYTHONPATH']=str(blocker);env['PYTHONDONTWRITEBYTECODE']='1';env['PYTHONIOENCODING']='utf-8';env['PYTHONNOUSERSITE']='1'
    steps=[
        ('original',['reconstruct_requests.py','--verify']),
        ('original',['recompute_results.py']),
        ('audits',['reproduce_audits.py']),
        ('new_experiment',['export_results.py','--run','run_v2','--output',str(out/'new_exports')]),
        ('new_experiment',['audit_and_figures/independent_result_audit.py','--experiment',str(work/'new_experiment'),'--output',str(out/'independent_audit.json')]),
        ('targeted_followup',['original_regret.py','--input','../original/request_block_map.csv','--output',str(out/'original_regret.json')]),
        ('targeted_followup',['analysis.py','--run','run','--output',str(out/'targeted_exports')]),
        ('targeted_followup',['audit_independent.py','--run','run','--exports',str(out/'targeted_exports')]),
    ]
    for folder,args in steps:
        print('Running:',folder,*args,flush=True)
        subprocess.run([sys.executable,'-s','-B',*args],cwd=work/folder,env=env,check=True)
    for name,digest in hashes.items():
        assert hashlib.sha256((source/name).read_bytes()).hexdigest()==digest,name
    (out/'PASSED.json').write_text(json.dumps({'passed':True,'verified_files':len(hashes),'api_calls':0,'archived_files_unchanged':True},indent=2)+'\n')
    print('Offline reproduction passed:',out)
if __name__=='__main__':main()
