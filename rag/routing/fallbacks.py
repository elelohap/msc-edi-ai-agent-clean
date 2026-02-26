# rag/routing/fallbacks.py

MDES_REDIRECT_MSG = (
    "I only answer questions about the MSc Engineering Design & Innovation (EDI) programme. "
    "For information about the MDes (Master of Design in Integrated Design), please refer to the official programme website https://cde.nus.edu.sg/did/mdes/."
)

NOT_FOUND_FALLBACK = (
    "I can’t find this in the MSc EDI admissions information I am currently using. "
    "If you rephrase your question, I may be able to help."
)

REQUIREMENT_FALLBACK_GENERIC = (
    "I can’t find a confirmed EDI-specific requirement statement for this in my current sources. "
    "Admissions are usually assessed holistically (academic background, projects/experience, and motivation)."
)

SUITABILITY_FALLBACK = (
    "Candidates who tend to thrive in MSc Engineering Design & Innovation (EDI) are typically curious about working across disciplines, "
    "comfortable with ambiguity, and motivated to solve real-world problems through design and technology. "
    "The programme suits people who enjoy collaboration and want to broaden beyond a single discipline."
)

PROGRAMME_START_FALLBACK = (
    "## Programme Start\n\n"
    "- MSc EDI typically has one intake per academic year.\n"
    "- Classes usually start in the second half of the year (often around August).\n"
    "- Please refer to your offer/enrolment instructions for the confirmed start date.\n"
)

OFFER_OUTCOME_FALLBACK = (
    "If you do not accept the offer within the acceptance period stated in your offer letter, "
    "the offer will typically lapse and you will not be enrolled in MSc Engineering Design & Innovation (EDI)."
)

REAPPLICATION_FALLBACK = (
    "Yes — you can apply again to MSc Engineering Design & Innovation (EDI) in a later application cycle. "
    "Each cycle is assessed independently."
)

VISA_FALLBACK = (
    "## Visa / Student Pass\n\n"
    "- If you are an international student, you may need a Student’s Pass to study at NUS.\n"
    "- Visa/Student’s Pass steps are typically provided after you accept an offer.\n"
)

VISA_PROCESS_FALLBACK = (
    "## Visa / Student Pass Process\n\n"
    "- Visa application is typically handled after you accept an offer.\n"
    "- NUS will provide official instructions for applying for a Student’s Pass.\n"
    "- The exact steps depend on your nationality.\n"
)
