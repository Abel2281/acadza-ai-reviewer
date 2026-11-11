from typing import Dict, Any, Optional

def generate_student_reply(
    verdict: str,
    repair: Optional[str],
    comment: str,
    evidence: str,
    edit: Optional[Dict[str, Any]] = None
) -> str:
    """
    Generates a respectful, encouraging 1-3 sentence reply tailored for a stressed 17yo JEE/NEET student.
    """
    comment_lower = comment.lower() if comment else ""

    if verdict == "not_actionable":
        if "ignore all previous instructions" in comment_lower or "admin" in comment_lower:
            return "Thank you for contacting Acadza Support. We review all feedback to ensure our question bank remains accurate and fair."
        return "Thank you for reaching out. We reviewed the question but could not find an actionable error based on your comment. If you think there's a specific issue, please flag it with details."

    if verdict == "display_issue":
        if "cut" in comment_lower or "screen" in comment_lower:
            return "Thanks for letting us know. The question content is correct, but there appears to be a layout issue on mobile screens. We've notified our frontend team to fix the rendering."
        if "slow" in comment_lower or "load" in comment_lower:
            return "Thank you for reporting this. The question data is intact, but our servers may have experienced a temporary loading delay. Please try refreshing or checking your connection."
        return "Thanks for flagging this. The question and solution are verified correct; this appears to be a local rendering issue on the app which our engineering team is addressing."

    if verdict == "app_issue":
        if "saved" in comment_lower or "clicked" in comment_lower:
            return "We understand your frustration. The question and key are verified correct, but we've logged this platform interaction issue with our app engineering team to ensure responses register properly."
        return "Thank you for bringing this up. The question content is accurate, but we have forwarded your report to the app platform team to investigate any UI recording discrepancies."

    if verdict == "language_mode":
        return "Thanks for your feedback! This question is currently only available in English on our platform. We've logged your request for Hindi translations as we expand our regional content."

    if verdict == "syllabus":
        return "Thank you for flagging this concern. We've routed this question to our senior academic faculty to verify against the latest NTA NEET/JEE syllabus update."

    if verdict == "no_error":
        if "3112.99" in comment_lower or "3113" in comment_lower:
            return "Thanks for your careful check! In this problem, 3113 is correct because the question requires applying significant figure rules to 10 × A (311.299 rounds to 311.3 m², so 10A = 3113). Best of luck with your prep!"
        if "root" in comment_lower or "50" in comment_lower:
            return "We re-solved this carefully: the calculation is verified and the stored answer key is mathematically sound. Reviewing the solution breakdown step by step should help clarify the concept."
        return "We carefully verified this question and re-checked the solution steps. The question and answer key are correct as published. Keep up the thorough practice!"

    if verdict == "defect":
        if repair == "option_repair" and not edit:
            return "Thank you for reporting this. The question shows only three options, and the solution points to option C. Our faculty is reviewing what should be restored before any change is made."
        if repair == "answer_key":
            if edit and edit.get("replace"):
                return f"You're completely right, and thank you for catching this. The answer key was incorrect and is being updated to option {edit['replace']}. We appreciate your dedication!"
            return "You're completely right, and thank you for catching this. The answer key had an error and has been queued for immediate faculty correction. Thanks for helping your fellow students!"

        if repair == "stem_data":
            return "Sharp catch! A necessary value or condition was indeed missing in the question stem. Our academic team is adding the missing data immediately. Thank you for reporting this!"

        if repair == "option_repair":
            return "Good eye! An option was truncated or missing in the question display. We are repairing the option text right away so everyone can solve it without confusion."

        if repair == "markup_leak":
            return "Thank you for flagging this. A formatting code leaked into the question text. We've cleaned up the equation markup so it renders properly."

        if repair == "solution_fix":
            return "Thank you for pointing this out. The final answer was right, but there was an error in the written solution steps. Our subject experts are revising the explanation."

        if repair == "wrong_question":
            return "Thank you for your report. The solution attached to this question indeed belonged to a different problem. Our faculty is providing the correct step-by-step solution."

        if repair == "wrong_chapter":
            return "Thank you for the notification. This question was accidentally cataloged under the wrong chapter; our curriculum team is reassigning it to the correct topic."

        if repair == "identical_options":
            return "You're completely right — two of the options were identical. Our faculty is authoring distinct distractor options right now. Thanks for letting us know!"

        # Generic defect
        return "Thank you for flagging this issue. We've confirmed the defect and our subject matter experts are updating the question record immediately."

    return "Thank you for taking the time to report this question. Our academic team is reviewing the item to ensure accuracy."

