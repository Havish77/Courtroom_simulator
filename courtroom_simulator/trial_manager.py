'''
from agents.judge import JudgeAgent
from agents.lawyer import DefenseAgent, ProsecutionAgent
from agents.defendant import DefendantAgent
from agents.witness import WitnessAgent

class TrialManager:
    def __init__(self, judge: JudgeAgent, defense: DefenseAgent, prosecution: ProsecutionAgent,
                 defendant: DefendantAgent, witnesses: list[WitnessAgent]):
        self.judge = judge
        self.defense = defense
        self.prosecution = prosecution
        self.defendant = defendant
        self.witnesses = witnesses
        self.ended = False

        self.step_queue = []
        self._prepare_steps()

    def _prepare_steps(self):
        # Opening statements
        self.step_queue.append(("open", self.prosecution))
        self.step_queue.append(("open", self.defense))
        self.step_queue.append(("judge_review", "opening"))

        # Witness examination
        for witness in self.witnesses:
            self.step_queue.append(("question", (self.prosecution, witness)))
            self.step_queue.append(("cross", (self.defense, witness)))
            self.step_queue.append(("judge_review", f"witness {witness.name}"))

        # Closing arguments
        self.step_queue.append(("close", self.prosecution))
        self.step_queue.append(("close", self.defense))
        self.step_queue.append(("verdict", self.judge))

    def _check_end_condition(self, statement: str) -> bool:
        endings = ["no further", "rest my case", "cannot justify", "have nothing more", "i concede"]
        return any(phrase in statement.lower() for phrase in endings)

    def _handle_objection(self, message: str, by_agent_name: str):
        if "objection" in message.lower():
            ruling = self.judge.respond(
                f"{by_agent_name} raised an objection: {message}\nPlease rule with 'sustained' or 'overruled'."
            )
            print(f"👨‍⚖️ Judge ruling: {ruling}")
            return ruling
        return None

    def run_next_step(self):
        if self.ended:
            print("⚖️ Trial has ended.")
            return

        if not self.step_queue:
            print("✅ Trial completed all steps.")
            self.ended = True
            return

        step_type, payload = self.step_queue.pop(0)

        if step_type == "open":
            agent = payload
            role = "Prosecution" if agent == self.prosecution else "Defense"
            print(f"\n📢 {role} Opening Statement:")
            msg = agent.respond("Present your opening statement.")
            if not msg or len(msg.strip()) < 10:
                msg = (
                    "The prosecution intends to prove the defendant’s guilt beyond a reasonable doubt."
                    if agent == self.prosecution else
                    "The defense contends that the defendant is not guilty and will provide evidence to support this."
                )
                print(f"(ℹ️ Using default {role.lower()} opening statement.)")
            print(msg)
            self._handle_objection(msg, role)
            if self._check_end_condition(msg):
                print(f"{role} has nothing further to say. Trial ending.")
                self.ended = True

        elif step_type == "question":
            lawyer, witness = payload
            print(f"\n🧑‍⚖️ {lawyer.__class__.__name__} questions witness {witness.name}")
            q = lawyer.respond(f"Question the witness {witness.name}.")
            self._handle_objection(q, lawyer.__class__.__name__)
            a = witness.respond(q)
            print(f"{witness.name} answers: {a}")

        elif step_type == "cross":
            lawyer, witness = payload
            print(f"\n🧑‍⚖️ {lawyer.__class__.__name__} cross-examines witness {witness.name}")
            cross = lawyer.respond(f"Cross-examine the witness {witness.name}.")
            self._handle_objection(cross, lawyer.__class__.__name__)
            a = witness.respond(cross)
            print(f"{witness.name} answers (cross): {a}")

        elif step_type == "judge_review":
            subject = payload
            print(f"\n👨‍⚖️ Judge reviewing: {subject}")
            review = self.judge.respond(f"Review and evaluate {subject}.")
            print("Judge:", review)

        elif step_type == "close":
            agent = payload
            role = "Prosecution" if agent == self.prosecution else "Defense"
            print(f"\n🔚 {role} Closing Argument:")
            msg = agent.respond("Make your closing argument.")
            self._handle_objection(msg, role)
            print(msg)
            if self._check_end_condition(msg):
                print(f"{role} has conceded or failed to justify. Ending trial.")
                self.ended = True

        elif step_type == "verdict":
            print("\n⚖️ Final Verdict from Judge:")
            verdict = self.judge.respond("Deliver your final verdict based on the trial.")
            print("🧑‍⚖️ Judge Verdict:", verdict)
            if any(word in verdict.lower() for word in ["guilty", "not guilty", "verdict"]):
                self.ended = True
            else:
                print("⚠️ Verdict not conclusive. Continuing possible re-evaluation...")
'''
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

        self.case_type = self._determine_case_type()
        self.plaintiff = PlaintiffAgent() if self.case_type == "civil" else None

        self.step_queue = []
        self._prepare_steps()

    def _determine_case_type(self) -> str:
        # Ask the judge LLM to classify the case type
        response = self.judge.respond("Is this a criminal or civil case? Just reply 'civil' or 'criminal'.")
        case_type = response.strip().lower()
        if "civil" in case_type:
            return "civil"
        return "criminal"

    def _prepare_steps(self):
        if self.case_type == "civil":
            self.step_queue.append(("open", self.plaintiff))
        else:
            self.step_queue.append(("open", self.prosecution))

        self.step_queue.append(("open", self.defense))
        self.step_queue.append(("judge_review", "opening"))

        for witness in self.witnesses:
            if self.case_type == "civil":
                self.step_queue.append(("question", (self.plaintiff, witness)))
            else:
                self.step_queue.append(("question", (self.prosecution, witness)))

            self.step_queue.append(("cross", (self.defense, witness)))
            self.step_queue.append(("judge_review", f"witness {witness.name}"))

        if self.case_type == "civil":
            self.step_queue.append(("close", self.plaintiff))
        else:
            self.step_queue.append(("close", self.prosecution))

        self.step_queue.append(("close", self.defense))
        self.step_queue.append(("verdict", self.judge))

    def _check_end_condition(self, statement: str) -> bool:
        endings = ["no further", "rest my case", "cannot justify", "have nothing more", "i concede"]
        return any(phrase in statement.lower() for phrase in endings)

    def _handle_objection(self, message: str, by_agent_name: str):
        if "objection" in message.lower():
            ruling = self.judge.respond(
                f"{by_agent_name} raised an objection: {message}\nPlease rule with 'sustained' or 'overruled'."
            )
            print(f"👨‍⚖️ Judge ruling: {ruling}")
            return ruling
        return None

    def run_next_step(self):
        if self.ended:
            print("⚖️ Trial has ended.")
            return

        if not self.step_queue:
            print("✅ Trial completed all steps.")
            self.ended = True
            return

        step_type, payload = self.step_queue.pop(0)

        if step_type == "open":
            agent = payload
            if self.case_type == "civil":
                role = "Plaintiff" if agent == self.plaintiff else "Defense"
            else:
                role = "Prosecution" if agent == self.prosecution else "Defense"

            print(f"\n📢 {role} Opening Statement:")
            msg = agent.respond("Present your opening statement.")
            if not msg or len(msg.strip()) < 10:
                if self.case_type == "civil":
                    msg = (
                        "The plaintiff intends to prove the defendant’s liability and seek fair compensation."
                        if agent == self.plaintiff else
                        "The defense denies liability and will contest the plaintiff’s claims."
                    )
                else:
                    msg = (
                        "The prosecution intends to prove the defendant’s guilt beyond a reasonable doubt."
                        if agent == self.prosecution else
                        "The defense contends that the defendant is not guilty and will provide evidence to support this."
                    )
                print(f"(ℹ️ Using default {role.lower()} opening statement.)")
            print(msg)
            self._handle_objection(msg, role)
            if self._check_end_condition(msg):
                print(f"{role} has nothing further to say. Trial ending.")
                self.ended = True

        elif step_type == "question":
            lawyer, witness = payload
            print(f"\n🧑‍⚖️ {lawyer.__class__.__name__} questions witness {witness.name}")
            q = lawyer.respond(f"Question the witness {witness.name}.")
            self._handle_objection(q, lawyer.__class__.__name__)
            a = witness.respond(q)
            print(f"{witness.name} answers: {a}")

        elif step_type == "cross":
            lawyer, witness = payload
            print(f"\n🧑‍⚖️ {lawyer.__class__.__name__} cross-examines witness {witness.name}")
            cross = lawyer.respond(f"Cross-examine the witness {witness.name}.")
            self._handle_objection(cross, lawyer.__class__.__name__)
            a = witness.respond(cross)
            print(f"{witness.name} answers (cross): {a}")

        elif step_type == "judge_review":
            subject = payload
            print(f"\n👨‍⚖️ Judge reviewing: {subject}")
            review = self.judge.respond(f"Review and evaluate {subject}.")
            print("Judge:", review)

        elif step_type == "close":
            agent = payload
            if self.case_type == "civil":
                role = "Plaintiff" if agent == self.plaintiff else "Defense"
            else:
                role = "Prosecution" if agent == self.prosecution else "Defense"

            print(f"\n🖚 {role} Closing Argument:")
            msg = agent.respond("Make your closing argument.")
            self._handle_objection(msg, role)
            print(msg)
            if self._check_end_condition(msg):
                print(f"{role} has conceded or failed to justify. Ending trial.")
                self.ended = True

        elif step_type == "verdict":
            print("\n⚖️ Final Verdict from Judge:")
            verdict = self.judge.respond("Deliver your final verdict based on the trial.")
            print("🧑‍⚖️ Judge Verdict:", verdict)
            if any(word in verdict.lower() for word in ["guilty", "not guilty", "verdict", "liable", "not liable"]):
                self.ended = True
            else:
                print("⚠️ Verdict not conclusive. Continuing possible re-evaluation...")
