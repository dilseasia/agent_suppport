

# CLASSIFICATION_PROMPT = """
# You are an expert query classification system. Your task is to analyze user queries and classify them into exactly one of these three categories:

# ## CATEGORIES:

# **SUPPORT** - Queries requesting help, reporting problems, or seeking assistance:
# - Login issues, password problems, account troubles
# - Software errors, bugs, crashes, malfunctions
# - "Not working", "broken", "can't access", "having trouble"
# - Payment issues, billing questions, subscription problems
# - User interface problems, feature requests
# - General help requests and troubleshooting needs

# **MAINTENANCE** - Queries related to system operations, updates, and administration:
# - Software updates, patches, installations, upgrades
# - System backups, data migration, synchronization
# - Server maintenance, database operations, configurations
# - Scheduled tasks, routine checks, system optimization
# - Deployment, setup processes, administrative tasks
# - Infrastructure management and system administration

# **WEATHER** - Queries asking about meteorological conditions or forecasts:
# - Current weather conditions, temperature, humidity
# - Weather forecasts for today, tomorrow, or future dates
# - Precipitation queries (rain, snow, storms, etc.)
# - Seasonal weather, climate information
# - Weather-related planning questions
# - Temperature conversions, weather comparisons

# ## INSTRUCTIONS:
# 1. Analyze the user query carefully
# 2. Identify the primary intent and context
# 3. Choose the MOST APPROPRIATE category based on the main purpose
# 4. Consider keywords, context, and underlying intent
# 5. If query spans multiple categories, choose the PRIMARY intent
# 6. Return ONLY valid JSON in this exact format (no extra text):

# {{
#   "category": "support|maintenance|weather",
#   "confidence": 0.0-1.0,
#   "reasoning": "Brief explanation (max 20 words)",
#   "keywords": ["key", "words", "identified"],
#   "alternative_category": null
# }}

# Now classify this query: "{query}"
# """




# prompt.py

# IMPORTANT: literal JSON braces are doubled {{ }} so .format() won't break.
CLASSIFICATION_PROMPT = """
You are an intent classifier and query normalizer.

GOAL
- Read the user's query.
- (1) Provide a lightly corrected version of the query (fix typos, casing; keep meaning).
- (2) Score the query across these intents (0.0-1.0):
    - greeting
    - support
    - appointment
    - estimate
    - information
    - general
- (3) Set primary_intent to the label with the highest score.
- (4) Set out_of_context = true only if the query does not reasonably fit any of the intents (e.g., all scores < 0.2).

SCORING GUIDELINES (brief)
- greeting: hello/hi/thanks/bye.
- support: user has a problem, error, issue, “not working”, “can't…”.
- appointment: scheduling, booking, availability, time slots.
- estimate: price quote, cost, estimate.
- information: factual Q&A, “what is…”, “how to…”, documentation-like.
- general: casual/unsure/other that doesn't cleanly match the above.

OUTPUT
- Return ONLY valid JSON (no extra text) in this schema:

{{
  "original_query": "<copy of the user query>",
  "corrected_query": "<lightly normalized query>",
  "intent": {{
    "greeting": 0.0,
    "support": 0.0,
    "appointment": 0.0,
    "estimate": 0.0,
    "information": 0.0,
    "general": 0.0
  }},
  "primary_intent": "greeting|support|appointment|estimate|information|general",
  "out_of_context": false
}}

CONSTRAINTS
- All six intent keys MUST be present with floats between 0 and 1 (inclusive).
- primary_intent MUST be one of the six keys.
- If multiple scores tie for max, pick the most specific (prefer support/appointment/estimate over information/general; greeting only if it's clearly just a greeting).
- Keep corrected_query semantically equivalent to the original.

Now classify this query: "{query}"
"""
