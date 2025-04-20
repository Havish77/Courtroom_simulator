from typing import Optional, Union, Tuple
from agents.judge import JudgeAgent
from agents.lawyer import DefenseAgent, ProsecutionAgent
from agents.defendant import DefendantAgent
from agents.witness import WitnessAgent
from agents.plaintiff import PlaintiffAgent

class TrialManager:
    def __init__(self, judge: JudgeAgent, defense: DefenseAgent, prosecution: ProsecutionAgent,
                 defendant: DefendantAgent, witnesses: list[WitnessAgent]):
        self.judge = judge
        self.defense = defense
        self.prosecution = prosecution
        self.defendant = defendant
        self.witnesses = witnesses
        self.ended = False
        self.current_phase = "not_started"  # opening, examination, closing, ended
        self.current_witness_index = -1
        
        self.case_type = self._determine_case_type()
        self.plaintiff = PlaintiffAgent() if self.case_type == "civil" else None
        
        # Track which side is currently presenting
        self.current_presenting_side = None  # prosecution/plaintiff or defense
        
        # Track objections
        self.pending_objection = None
        
        # Phases in order
        self.phases = [
            "opening_statements",
            "prosecution_case",
            "defense_case",
            "closing_arguments",
            "verdict"
        ]
        self.current_phase_index = -1
        
    def _determine_case_type(self) -> str:
        response = self.judge.respond("Is this a criminal or civil case? Just reply 'civil' or 'criminal'.")
        return "civil" if "civil" in response.strip().lower() else "criminal"
    
    def _next_phase(self):
        self.current_phase_index += 1
        if self.current_phase_index >= len(self.phases):
            self.ended = True
            return
        
        self.current_phase = self.phases[self.current_phase_index]
        
        if self.current_phase == "opening_statements":
            self.current_presenting_side = "prosecution" if self.case_type == "criminal" else "plaintiff"
        elif self.current_phase == "prosecution_case":
            self.current_presenting_side = "prosecution" if self.case_type == "criminal" else "plaintiff"
            self.current_witness_index = 0
        elif self.current_phase == "defense_case":
            self.current_presenting_side = "defense"
            self.current_witness_index = 0
        elif self.current_phase == "closing_arguments":
            self.current_presenting_side = "prosecution" if self.case_type == "criminal" else "plaintiff"
    
    def _get_current_lawyer(self) -> Union[ProsecutionAgent, DefenseAgent, PlaintiffAgent]:
        if self.current_presenting_side == "defense":
            return self.defense
        elif self.current_presenting_side == "prosecution":
            return self.prosecution
        elif self.current_presenting_side == "plaintiff":
            return self.plaintiff
        return None
    
    def _switch_presenting_side(self):
        if self.current_presenting_side == "defense":
            self.current_presenting_side = "prosecution" if self.case_type == "criminal" else "plaintiff"
        else:
            self.current_presenting_side = "defense"
    
    def _handle_objection(self, message: str, by_agent_name: str) -> Tuple[bool, str]:
        """Returns (was_there_objection, ruling)"""
        if "objection" in message.lower():
            self.pending_objection = (message, by_agent_name)
            return True, None
        return False, None
    
    def _process_objection(self) -> str:
        if not self.pending_objection:
            return None
            
        message, by_agent_name = self.pending_objection
        self.pending_objection = None
        
        ruling = self.judge.respond(
            f"{by_agent_name} raised an objection: {message}\n"
            "Please rule with 'sustained' or 'overruled' and briefly explain."
        )
        print(f"👨‍⚖️ Judge rules on objection: {ruling}")
        return ruling
    
    def _check_end_condition(self, statement: str) -> bool:
        endings = [
            "no further questions", 
            "rest my case", 
            "nothing further",
            "conclude my presentation"
        ]
        statement_lower = statement.lower()
        return any(phrase in statement_lower for phrase in endings)
    
    def run_next_step(self):
        if self.ended:
            print("⚖️ Trial has concluded.")
            return
        
        # Handle any pending objections first
        if self.pending_objection:
            self._process_objection()
            return
        
        # Move to next phase if needed
        if self.current_phase_index == -1 or self.current_phase == "ended":
            self._next_phase()
            return
        
        # Execute current phase
        if self.current_phase == "opening_statements":
            self._run_opening_statements()
        elif self.current_phase in ["prosecution_case", "defense_case"]:
            self._run_examination()
        elif self.current_phase == "closing_arguments":
            self._run_closing_arguments()
        elif self.current_phase == "verdict":
            self._run_verdict()
    
    def _run_opening_statements(self):
        lawyer = self._get_current_lawyer()
        side = "Prosecution" if self.case_type == "criminal" else "Plaintiff" if self.current_presenting_side == "plaintiff" else "Defense"
        
        print(f"\n📢 {side} Opening Statement:")
        statement = lawyer.respond("Present your opening statement to the court.")
        print(statement)
        
        # Check for objections in the statement
        self._handle_objection(statement, f"{side} during opening")
        
        # Switch sides or move to next phase
        if self.current_presenting_side == "defense":
            self._next_phase()  # Move to examination phase
        else:
            self._switch_presenting_side()
    
    def _run_examination(self):
        # Check if we've examined all witnesses for this side
        if self.current_witness_index >= len(self.witnesses):
            self._next_phase()
            return
        
        witness = self.witnesses[self.current_witness_index]
        lawyer = self._get_current_lawyer()
        opposing_lawyer = self.defense if lawyer == self.prosecution or lawyer == self.plaintiff else self.prosecution if self.case_type == "criminal" else self.plaintiff
        
        # Direct examination
        print(f"\n🔍 {lawyer.__class__.__name__} examining {witness.name}:")
        question = lawyer.respond(f"Ask {witness.name} a relevant question.")
        print(f"Q: {question}")
        
        # Check for objection from opposing counsel
        objection = opposing_lawyer.respond(
            f"The {lawyer.__class__.__name__} asked: '{question}'\n"
            "Should you object? If so, state 'Objection' and the reason. Otherwise say 'No objection'."
        )
        
        if "no objection" not in objection.lower():
            obj_raised, _ = self._handle_objection(objection, opposing_lawyer.__class__.__name__)
            if obj_raised:
                return  # Stop here to process objection next step
        
        # If no objection or it was overruled, witness answers
        answer = witness.respond(question)
        print(f"A: {answer}")
        
        # Check if lawyer is done with this witness
        if self._check_end_condition(question):
            self.current_witness_index += 1
    
    def _run_closing_arguments(self):
        lawyer = self._get_current_lawyer()
        side = "Prosecution" if self.case_type == "criminal" else "Plaintiff" if self.current_presenting_side == "plaintiff" else "Defense"
        
        print(f"\n🖚 {side} Closing Argument:")
        statement = lawyer.respond("Present your closing argument to the court.")
        print(statement)
        
        # Check for objections
        self._handle_objection(statement, f"{side} during closing")
        
        # Switch sides or move to verdict
        if self.current_presenting_side == "defense":
            self._next_phase()  # Move to verdict
        else:
            self._switch_presenting_side()
    
    def _run_verdict(self):
        print("\n⚖️ Judge deliberating...")
        verdict = self.judge.respond(
            "Based on all evidence and arguments presented, "
            "please deliver your verdict. Explain your reasoning "
            "and conclude with 'I find the defendant [guilty/not guilty]' "
            "or '[liable/not liable]' as appropriate."
        )
        print("🧑‍⚖️ Judge's Verdict:", verdict)
        self.ended = True
