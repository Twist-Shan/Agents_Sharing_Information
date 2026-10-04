"""Nonfrozen terminal reader dispatch for downstream reports; no paid imports."""
from pathlib import Path
from contextlib import contextmanager
import runtime

HERE=Path(__file__).resolve().parent


def require(ok,label):
    if not ok:raise ValueError('terminal_reader:'+label)


def modules_for_manifest(manifest):
    signature=(manifest.get('version'),manifest.get('kind'))
    if signature==(2,'MISSING_ONLY_EXTENDED_RESPONSE_SUPPLEMENT'):
        import supplement_contract as contract
        import export_completion as exporter
    elif signature==(3,'USER_AUTHORIZED_DEEPSEEK_2048_COMPLETION'):
        import ceiling2048_contract as contract
        import export_ceiling2048 as exporter
    else:raise ValueError('terminal_reader:unsupported_manifest_kind_or_version')
    return contract,exporter


def source_hashes(verified):
    version=verified.manifest.get('version',2)
    require(version in (2,3),'unsupported_verified_version')
    names=['terminal_reader.py','export_validation.py',
           'ceiling2048_contract.py' if version==3 else 'supplement_contract.py',
           'export_ceiling2048.py' if version==3 else 'export_completion.py']
    return {name:runtime.sha(HERE/name) for name in names}


def token_history(verified):
    return [128,512,2048] if verified.manifest.get('version')==3 else [128,512]


def unchanged(verified,contract):
    return all(runtime.sha(contract.contained_file(n))==h for n,h in verified.input_sha256.items())


def guard_output(verified,contract,run,output):
    """Keep every inherited source and its exports separate from new report files."""
    bases=[contract.contained_file(verified.manifest['source_run_relative'])]
    for name in ('source_run_relative','original_source_directory','source512_run_relative'):
        if name in verified.source_binding:bases.append(contract.contained_file(verified.source_binding[name]))
    for name in ('source_closure_relative','source512_closure_relative'):
        relative=verified.source_binding.get(name)
        if relative:bases.append(contract.contained_file(relative).parent)
    bases.append(Path(run).resolve()/'terminal_export')
    output=Path(output).resolve()
    require(output!=Path(run).resolve() and all(output!=base and not output.is_relative_to(base) for base in bases),'output_overlaps_preserved_source')


def read_bound_export(run,verified,exporter):
    folder=Path(run)/'terminal_export';em=runtime.read(folder/'export_manifest.json')
    require(em.get('status')=='passed' and em.get('manifest_sha256')==verified.manifest['manifest_sha256']
            and em.get('execution_layer')==exporter.LAYER,'export_identity')
    for name,digest in em['files_sha256'].items():
        require(Path(name).name==name and runtime.sha(folder/name)==digest,'export_member_changed')
    audit=runtime.read(folder/'operational_audit.json')
    require(audit['input_sha256']==verified.input_sha256 and audit['exporter_sha256']==runtime.sha(exporter.__file__),'export_source_binding')
    return em,audit


@contextmanager
def verified_run(run):
    run=Path(run).resolve();contract,exporter=modules_for_manifest(runtime.read(run/'manifest.json'))
    terminal=getattr(contract,'TERMINAL',runtime.TERMINAL)
    require(runtime.read(run/'status.json').get('state') in terminal,'not_terminal')
    with runtime.execution_lock(run/contract.LOCK):
        with runtime.execution_lock(run/'execution.lock'):
            verified=exporter.verify_locked(run)
            require(unchanged(verified,contract),'inputs_changed_before_report')
            yield verified,contract,exporter
            require(unchanged(verified,contract),'inputs_changed_during_report')
