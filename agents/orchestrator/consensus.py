from agents.execution.schemas import AnalysisSignal
from agents.shared.exceptions import ConsensusFailError
from pydantic import BaseModel

class ConsensusResult(BaseModel):
    consensus_match: bool
    signal: str

def deterministic_consensus_gate(fa: AnalysisSignal, ta: AnalysisSignal) -> ConsensusResult:
    if fa.signal != ta.signal:
        raise ConsensusFailError(f"Signals conflict: {fa.signal} vs {ta.signal}")
    return ConsensusResult(consensus_match=True, signal=fa.signal)
