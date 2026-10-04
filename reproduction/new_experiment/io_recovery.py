"""Operational-only recovery: retry an atomic replacement on Windows sharing errors.

Frozen science, HTTP payloads, answer classification, retry limits, and accounting
remain in runtime.py. Original sources and journals are never overwritten here.
"""
from pathlib import Path
import argparse,os,time
import runtime

def resilient_save(path,value):
    path=Path(path)
    temporary=path.with_suffix(path.suffix+'.writing')
    with temporary.open('w',encoding='utf-8',newline='\n') as file:
        file.write(runtime.compact(value)+'\n')
        file.flush()
        os.fsync(file.fileno())
    for attempt in range(30):
        try:
            os.replace(temporary,path)
            return
        except PermissionError:
            if attempt==29:raise
            time.sleep(.2)

def execute(run):
    runtime.validate(run)
    runtime.save=resilient_save
    runtime.execute(run)

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--run',type=Path,default=Path(__file__).parent/'run_v2')
    args=parser.parse_args()
    execute(args.run)
