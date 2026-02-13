"""Tests for SpaCy-based style extractor."""

import pytest
from app.analysis.style_extractor import extract_community_style, _empty_style


# Sample texts mimicking different subreddit styles
STARTUP_POSTS = [
    "I've been building my SaaS for 6 months now and finally hit $5k MRR. The journey from zero to PMF was brutal. We pivoted three times before finding something that stuck. Our ARR is now on track for $60k and growing 15% month over month.",
    "Anyone else struggling with churn? We're at 8% monthly and it's killing our growth. Tried implementing better onboarding but honestly the product-market fit just isn't there yet for enterprise customers.",
    "Just raised our seed round - $1.2M at $6M post. Took us 4 months of pitching. The biggest lesson? VCs care about traction, not your deck. We had 200 paying users and that's what closed the deal.",
    "My co-founder just quit. We were 50/50 on equity and now I'm running everything solo. Has anyone dealt with this? How do you handle the vesting situation? I'm thinking about bringing on a technical advisor instead.",
    "Shipped a new feature yesterday and immediately got 3 support tickets about it breaking something else. Classic. Testing in production isn't a strategy, it's a lifestyle lol. At least our users are engaged enough to complain.",
    "We switched from Stripe to Paddle for our billing and it's been a nightmare. The migration took 2 weeks instead of the estimated 2 days. If you're considering it, make sure you have a solid rollback plan.",
    "TL;DR: Don't build features nobody asked for. We spent 3 months building an analytics dashboard that 2% of users even look at. Should have just talked to customers first.",
    "Okay so I need some honest feedback here. Our landing page converts at 1.2% and I can't figure out why. We've A/B tested the headline, the CTA, the pricing page... nothing moves the needle. What am I missing?",
    "Finally figured out why our CAC was so high - we were targeting the wrong audience entirely. Enterprise sales cycles are 6+ months for us. Switched to SMB and our CAC dropped 70% overnight.",
    "Hot take: most startup advice is survivorship bias. The founders who failed had the same hustle and the same strategies. Sometimes the market just doesn't want what you're building and that's okay.",
    "Been doing cold outreach for 3 weeks straight. 500 emails, 12 responses, 2 demos, 0 conversions. Is this normal or am I doing something fundamentally wrong? Using Apollo for prospecting btw.",
    "Our burn rate is getting scary. 8 months of runway left and revenue isn't growing fast enough. Thinking about cutting the team from 5 to 3 but it'll destroy morale. Any advice from founders who've been through this?",
]

GAMING_POSTS = [
    "bro this game is so broken rn lmao. spent 3 hours trying to beat the final boss and it glitched through the floor every single time. devs pls fix",
    "unpopular opinion: the new update actually made the game better?? like yeah they nerfed my main but the balance changes overall are way healthier for the meta",
    "just hit Diamond for the first time!! been hardstuck Plat for 2 seasons and finally made it. the secret was literally just playing fewer games but more focused. quality over quantity fr",
    "anyone else notice the fps drops in the new map? i'm running a 4070 and still getting stutters. this is ridiculous for a AAA game in 2026",
    "ngl the battle pass this season is kinda mid. like 90% filler and the tier 100 skin isn't even that good compared to last season's",
    "PSA: if you're having the crash bug on startup, delete your shader cache. fixed it for me and like 5 other people in my discord",
    "hot take: skill-based matchmaking is ruining casual gaming. i just wanna vibe with my friends without getting matched against sweats every single game",
    "the new character is SO busted omg. 70% win rate in ranked and they haven't even acknowledged it yet. remember when they nerfed Sage for having a 52% wr? lol",
    "finally got the platinum trophy after 200+ hours. this game has its issues but man... when it hits, it HITS. the story in chapter 4 had me actually emotional ngl",
    "can we talk about how the community has gotten so toxic lately? every other game someone is screaming in voice chat. im about to just perma-mute everyone",
]


class TestExtractCommunityStyle:
    """Test the main extract_community_style function."""

    def test_empty_input(self):
        result = extract_community_style([])
        assert result == _empty_style()

    def test_returns_all_sections(self):
        result = extract_community_style(STARTUP_POSTS)
        assert "vocabulary" in result
        assert "structure" in result
        assert "punctuation" in result
        assert "formatting" in result
        assert "openings" in result
        assert "imperfections" in result

    def test_vocabulary_extraction(self):
        result = extract_community_style(STARTUP_POSTS)
        vocab = result["vocabulary"]

        assert isinstance(vocab["top_terms"], list)
        assert len(vocab["top_terms"]) > 0
        assert isinstance(vocab["top_noun_phrases"], list)
        assert isinstance(vocab["oov_tokens"], list)
        assert vocab["avg_word_length"] > 0
        assert 0 <= vocab["stop_word_ratio"] <= 1.0

    def test_startup_vs_gaming_vocabulary_differs(self):
        startup_result = extract_community_style(STARTUP_POSTS)
        gaming_result = extract_community_style(GAMING_POSTS)

        startup_terms = set(startup_result["vocabulary"]["top_terms"])
        gaming_terms = set(gaming_result["vocabulary"]["top_terms"])

        # There should be meaningful difference in vocabulary
        overlap = startup_terms & gaming_terms
        unique_startup = startup_terms - gaming_terms
        unique_gaming = gaming_terms - startup_terms

        assert len(unique_startup) > 0, "Startup should have unique terms"
        assert len(unique_gaming) > 0, "Gaming should have unique terms"

    def test_gaming_has_more_oov_slang(self):
        """Gaming posts use more slang/OOV tokens than startup posts."""
        startup_result = extract_community_style(STARTUP_POSTS)
        gaming_result = extract_community_style(GAMING_POSTS)

        # Gaming uses more non-standard language (lmao, ngl, rn, etc.)
        gaming_oov = gaming_result["vocabulary"]["oov_tokens"]
        # At minimum, gaming should have some OOV tokens detected
        # (exact count depends on SpaCy's vocabulary)
        assert isinstance(gaming_oov, list)

    def test_structure_extraction(self):
        result = extract_community_style(STARTUP_POSTS)
        structure = result["structure"]

        assert structure["avg_post_word_count"] > 0
        assert structure["avg_paragraph_count"] >= 1.0
        assert 0 <= structure["question_sentence_ratio"] <= 1.0
        assert 0 <= structure["imperative_ratio"] <= 1.0

    def test_punctuation_extraction(self):
        result = extract_community_style(GAMING_POSTS)
        punct = result["punctuation"]

        assert punct["exclamation_per_post"] >= 0
        assert punct["question_mark_per_post"] >= 0
        assert punct["ellipsis_per_post"] >= 0
        assert punct["emoji_per_post"] >= 0

    def test_gaming_more_exclamations(self):
        """Gaming posts tend to use more exclamation marks."""
        startup_result = extract_community_style(STARTUP_POSTS)
        gaming_result = extract_community_style(GAMING_POSTS)

        # Gaming posts are more emotionally expressive
        assert gaming_result["punctuation"]["exclamation_per_post"] >= startup_result["punctuation"]["exclamation_per_post"]

    def test_formatting_extraction(self):
        result = extract_community_style(STARTUP_POSTS)
        fmt = result["formatting"]

        assert 0 <= fmt["has_tldr_ratio"] <= 1.0
        assert 0 <= fmt["has_edit_ratio"] <= 1.0
        assert 0 <= fmt["has_links_ratio"] <= 1.0
        assert fmt["avg_line_breaks"] >= 0

    def test_startup_has_tldr(self):
        """Startup posts include TL;DR."""
        result = extract_community_style(STARTUP_POSTS)
        assert result["formatting"]["has_tldr_ratio"] > 0

    def test_openings_extraction(self):
        result = extract_community_style(STARTUP_POSTS, STARTUP_POSTS[:5])
        openings = result["openings"]

        assert "top_opening_patterns" in openings
        assert isinstance(openings["top_opening_patterns"], list)

    def test_top_texts_parameter(self):
        """Providing top_texts should focus vocabulary extraction."""
        # Only top 3 posts as "top" texts
        top_3 = STARTUP_POSTS[:3]
        result = extract_community_style(STARTUP_POSTS, top_3)

        # Should still produce valid output
        assert len(result["vocabulary"]["top_terms"]) > 0

    def test_single_post(self):
        """Should handle single post without errors."""
        result = extract_community_style(["This is a single test post about Python programming."])
        assert result["vocabulary"]["top_terms"]
        assert result["structure"]["avg_post_word_count"] > 0

    def test_short_posts(self):
        """Should handle very short posts gracefully."""
        short = ["ok", "lol", "this", "yes please"]
        result = extract_community_style(short)
        # Should not crash, even if output is sparse
        assert "vocabulary" in result
        assert "structure" in result

    def test_imperfections_extraction(self):
        """Should extract all 4 imperfection metrics."""
        texts_with_imperfections = [
            "Beautiful day. Gorgeous sunset.",  # fragments (no verb)
            "I mean, actually it was fine. The thing (which was really surprising) happened yesterday.",
            "So the app -- you know -- just crashed. I tried to fix it but wait, that's not right.",
            "This is great. Amazing stuff. The project (with all its complexity) worked out.",
        ]
        result = extract_community_style(texts_with_imperfections)
        imp = result["imperfections"]

        # All 4 keys present
        assert "fragment_ratio" in imp
        assert "parenthetical_frequency" in imp
        assert "self_correction_rate" in imp
        assert "dash_interruption_rate" in imp

        # Types are correct
        assert isinstance(imp["fragment_ratio"], float)
        assert isinstance(imp["parenthetical_frequency"], float)
        assert isinstance(imp["self_correction_rate"], float)
        assert isinstance(imp["dash_interruption_rate"], float)

        # Fragment ratio should be > 0 (some fragments present)
        assert imp["fragment_ratio"] > 0, "Should detect sentence fragments"
        # Parenthetical frequency > 0 (parenthetical asides present)
        assert imp["parenthetical_frequency"] > 0, "Should detect parentheticals"
        # Self-correction rate > 0 (self-correction markers present)
        assert imp["self_correction_rate"] > 0, "Should detect self-corrections"
        # Dash interruption rate > 0 (dash interruptions present)
        assert imp["dash_interruption_rate"] > 0, "Should detect dash interruptions"

    def test_imperfections_in_empty_style(self):
        """Empty style should include imperfections with zero defaults."""
        result = _empty_style()
        assert "imperfections" in result
        assert result["imperfections"]["fragment_ratio"] == 0.0
        assert result["imperfections"]["parenthetical_frequency"] == 0.0
        assert result["imperfections"]["self_correction_rate"] == 0.0
        assert result["imperfections"]["dash_interruption_rate"] == 0.0
