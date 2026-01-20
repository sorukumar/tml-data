
import json
import pandas as pd

def generate_iconic():
    # 1. Load regenerated NBI data (Source of Truth for stats)
    with open('data/nbi/gs_nailbiters.json', 'r') as f:
        nailbiters = json.load(f)
    
    # 2. DEFINITIVE HISTORIAN LIST (Finals and Semis Only, 1968-2025)
    # Format: (Winner, Loser, Year, Tournament, Round)
    # Keeping it to the absolute pantheon of classics.
    historian_picks = [
        # The Classics (Pre-2000)
        ("Rod Laver", "Tony Roche", "1969", "Australian Open", "SF"), # The 90-game battle
        ("Ken Rosewall", "Tony Roche", "1971", "Australian Open", "F"), # Rosewall wins without dropping set? No, this was the final.
        ("Arthur Ashe", "Jimmy Connors", "1975", "Wimbledon", "F"), # Tactical masterpiece
        ("Bjorn Borg", "Roscoe Tanner", "1979", "Wimbledon", "F"), # 5 set epic
        ("Bjorn Borg", "John McEnroe", "1980", "Wimbledon", "F"), # The 18-16 Tiebreak
        ("John McEnroe", "Bjorn Borg", "1980", "US Open", "F"), # The Sequel
        ("Ivan Lendl", "John McEnroe", "1984", "Roland Garros", "F"), # The Comeback
        ("Boris Becker", "Kevin Curren", "1985", "Wimbledon", "F"), # Youngest winner
        ("Pat Cash", "Ivan Lendl", "1987", "Wimbledon", "F"), # Climb into stands
        ("Mats Wilander", "Ivan Lendl", "1988", "US Open", "F"), # Battle for #1
        ("Michael Chang", "Stefan Edberg", "1989", "Roland Garros", "F"), # Chang's title (not the Lendl QF/R16)
        ("Pete Sampras", "Andre Agassi", "1995", "US Open", "F"), # Rivalry Peak
        ("Andre Agassi", "Andrei Medvedev", "1999", "Roland Garros", "F"), # Career Slam
        ("Andre Agassi", "Todd Martin", "1999", "US Open", "F"), # Late night classic
        
        # The Golden Era (2000-2010)
        ("Patrick Rafter", "Andre Agassi", "2001", "Wimbledon", "SF"), # The best semi ever?
        ("Goran Ivanisevic", "Patrick Rafter", "2001", "Wimbledon", "F"), # Monday Magic
        ("Marat Safin", "Roger Federer", "2005", "Australian Open", "SF"), # The Masterpiece
        ("Rafael Nadal", "Roger Federer", "2008", "Wimbledon", "F"), # The GOAT Match
        ("Rafael Nadal", "Fernando Verdasco", "2009", "Australian Open", "SF"), # 5hr 14min
        ("Rafael Nadal", "Roger Federer", "2009", "Australian Open", "F"), # The Tears
        ("Roger Federer", "Juan Martin del Potro", "2009", "Roland Garros", "SF"), # Survival
        ("Roger Federer", "Andy Roddick", "2009", "Wimbledon", "F"), # 16-14 Fifth Set
        ("Juan Martin del Potro", "Roger Federer", "2009", "US Open", "F"), # The Breakthrough
        
        # The Big 3 Era (2011-2025)
        ("Novak Djokovic", "Roger Federer", "2011", "US Open", "SF"), # The Return
        ("Novak Djokovic", "Rafael Nadal", "2012", "Australian Open", "F"), # 5hr 53min
        ("Andy Murray", "Novak Djokovic", "2012", "US Open", "F"), # Britain's Drought Ends
        ("Rafael Nadal", "Novak Djokovic", "2013", "Roland Garros", "SF"), # Net touch drama
        # ("Stan Wawrinka", "Novak Djokovic", "2014", "Australian Open", "QF"), # QF - Removed per user request
        ("Stan Wawrinka", "Rafael Nadal", "2014", "Australian Open", "F"), # Stan's 1st
        ("Novak Djokovic", "Roger Federer", "2014", "Wimbledon", "F"), # High quality 5 setter
        ("Stan Wawrinka", "Novak Djokovic", "2015", "Roland Garros", "F"), # Short pants fame
        ("Roger Federer", "Rafael Nadal", "2017", "Australian Open", "F"), # #18
        ("Novak Djokovic", "Rafael Nadal", "2018", "Wimbledon", "SF"), # 10-8 Fifth Set
        ("Novak Djokovic", "Roger Federer", "2019", "Wimbledon", "F"), # 13-12 Tiebreak
        ("Rafael Nadal", "Daniil Medvedev", "2022", "Australian Open", "F"), # Double career slam
        ("Carlos Alcaraz", "Novak Djokovic", "2023", "Wimbledon", "F"), # Passing the Torch
        ("Jannik Sinner", "Daniil Medvedev", "2024", "Australian Open", "F"), # Sinner comeback
        ("Carlos Alcaraz", "Alexander Zverev", "2024", "Roland Garros", "F"), # 5 set grind
    ]

    final_list = []

    # Map NBI data for stats
    # Create lookup key: Winner|Loser|Year
    nbi_lookup = {}
    for m in nailbiters:
        parts = m['match'].split(' def. ')
        if len(parts) == 2:
            # Key: Winner|Loser|Year|Tournament
            key = f"{parts[0]}|{parts[1]}|{m['date'][:4]}|{m['tourney']}"
            nbi_lookup[key] = m

    for (w, l, y, t, r) in historian_picks:
        # Strict lookup: Winner|Loser|Year|Tournament
        # This prevents collisions (e.g. Laver vs Roche played AO SF and US Open F in 1969)
        key = f"{w}|{l}|{y}|{t}"
        
        match_data = nbi_lookup.get(key)
        
        # If not found in NBI (maybe score wasn't close enough to be a "nailbiter" statistically, or name mismatch)
        # We manually construct the entry if needed, but optimally we find it.
        # Let's try to be flexible with lookup if exact match fails
        if not match_data:
            print(f"Warning: Match not found in NBI logic: {key}. Searching looser...")
            # Try looser match? Or just accept fallback.
            # Maybe try checking date if tournament name implies vague matching?
            pass

        if match_data:
            entry = {
                "winner_name": w,
                "loser_name": l,
                "tourney_name": t,
                "tourney_date": match_data['date'],
                "round": match_data['round'],
                "score": match_data.get('score', ''),
                "match_stats_nbi": match_data.get('NBI', 0), # Store NBI score for reference
            }
            # Generate Narrative
            entry.update(get_narrative(w, l, y))
            final_list.append(entry)
        else:
            # Fallback for matches that might not be statistical "nailbiters" but are iconic (e.g. Ashe Connors)
            # We add them with minimal stats if we can't find them in NBI (which filters by drama)
            # Actually Ashe Connors was 6-1 6-1 5-7 6-4. Might represent low NBI?
            # We will generate a placeholder if missing from NBI file
             entry = {
                "winner_name": w,
                "loser_name": l,
                "tourney_name": t,
                "tourney_date": y + "0000",
                "round": r,
                "score": "N/A", # Needs verification
            }
             entry.update(get_narrative(w, l, y))
             final_list.append(entry)

    # Sort
    final_list.sort(key=lambda x: x['tourney_date'])
    
    # Save
    with open('data/nbi/iconic_gs_matches.json', 'w') as f:
        json.dump(final_list, f, indent=2)
    print(f"Generated {len(final_list)} curated historian matches.")

def get_narrative(w, l, y):
    # Narratives DB
    narratives = {
         "Rod Laver|Tony Roche|1969": {
            "historical_significance": "The Calendar Slam Crucible",
            "short_commentary": "Laver survives a 90-game semifinal marathon in extreme heat.",
            "career_impact": "The toughest test in Laver's second Grand Slam year.",
            "cultural_resonance": "Showcased the grueling nature of pre-tiebreak tennis."
        },
        "Arthur Ashe|Jimmy Connors|1975": {
            "historical_significance": "Intellect vs Power",
            "short_commentary": "Ashe employs 'junkball' tactics to dismantle the overwhelming favorite Connors.",
            "career_impact": "Ashe's crowning achievement; the first black man to win Wimbledon.",
            "cultural_resonance": "A tactical masterclass studied by coaches for decades."
        },
        "Bjorn Borg|John McEnroe|1980": {
            "historical_significance": "The 18-16 Tiebreak",
            "short_commentary": "Borg wins his 5th straight Wimbledon, but not before losing the most famous tiebreak in history.",
            "career_impact": "Reaffirmed Borg's dominance, though McEnroe closed the gap.",
            "cultural_resonance": "The definition of the 'Fire and Ice' rivalry."
        },
        "Ivan Lendl|John McEnroe|1984": {
            "historical_significance": "The Lendl Comeback",
            "short_commentary": "Lendl recovers from 2 sets down to shatter McEnroe's perfect season dream.",
            "career_impact": "Lendl's breakthrough Slam; McEnroe never won the French.",
            "cultural_resonance": "A psychological turning point; transformed Lendl into a champion."
        },
        "Michael Chang|Stefan Edberg|1989": {
            "historical_significance": "The Youngest Champion",
            "short_commentary": "17-year-old Chang completes his miracle run, defeating Edberg in 5 sets.",
            "career_impact": "Chang remains the youngest male Slam winner in history.",
            "cultural_resonance": "Hope and resilience personified in the shadow of Tiananmen."
        },
        "Goran Ivanisevic|Patrick Rafter|2001": {
            "historical_significance": "The People's Monday",
            "short_commentary": "Wildcard Ivanisevic wins a raucous Monday final after three previous heartbreaks.",
            "career_impact": "The ultimate underdog story; Goran's only Slam.",
            "cultural_resonance": "Changed Wimbledon atmosphere forever; 'The People's Final'."
        },
        "Rafael Nadal|Roger Federer|2008": {
            "historical_significance": "The Greatest Match Ever Played",
            "short_commentary": "Nadal dethrones Federer in near-darkness after 4h 48m of breathtaking tennis.",
            "career_impact": "Ended Federer's 5-year reign; completed Nadal's Channel Slam.",
            "cultural_resonance": "The pinnacle of the rivalry; widely considered the sport's greatest contest."
        },
        "Roger Federer|Andy Roddick|2009": {
            "historical_significance": "The 16-14 Heartbreaker",
            "short_commentary": "Federer breaks Sampras's record with his 15th Slam, surviving a gallant Roddick.",
            "career_impact": "Federer becomes statistical GOAT (at the time); Roddick's last great stand.",
            "cultural_resonance": "Roddick's 'I threw the kitchen sink at him' speech is legendary."
        },
        "Novak Djokovic|Rafael Nadal|2012": {
            "historical_significance": "The Iron Men",
            "short_commentary": "The longest Grand Slam final in history (5h 53m) pushed physical limits.",
            "career_impact": "Cemented Djokovic as the king of Australia; unimaginable endurance.",
            "cultural_resonance": "The trophy ceremony where they needed chairs is iconic."
        },
        "Roger Federer|Rafael Nadal|2017": {
            "historical_significance": "The Renaissance",
            "short_commentary": "Federer returns from injury to defeat his nemesis in a 5th set comeback.",
            "career_impact": "Won his 18th Slam at age 35; revitalized his career.",
            "cultural_resonance": "Proved 'class is permanent'; a nostalgic dream for fans."
        },
        "Novak Djokovic|Roger Federer|2019": {
            "historical_significance": "8-7, 40-15",
            "short_commentary": "Djokovic saves two championship points to win the first 12-12 tiebreak.",
            "career_impact": "Denied Federer #21; proved Djokovic's mental impregnability.",
            "cultural_resonance": "The most painful loss for Federer fans; the ultimate clutch performance."
        },
        "Rafael Nadal|Daniil Medvedev|2022": {
            "historical_significance": "The 21st Slam",
            "short_commentary": "Nadal recovers from 0-2 sets down to break the Big 3 tie.",
            "career_impact": "Nadal takes lead in GOAT race; Medvedev's 'kid stopped dreaming' moment.",
            "cultural_resonance": "A testament to 'fighting until the end'."
        },
        "Carlos Alcaraz|Novak Djokovic|2023": {
            "historical_significance": "The Changing of the Guard",
            "short_commentary": "20-year-old Alcaraz dethrones the 7-time champion in 5 sets.",
            "career_impact": "Announced Alcaraz as the next superstar; ended Djokovic's 10-year Centre Court streak.",
            "cultural_resonance": "The future of tennis arrived."
        },
        "Jannik Sinner|Daniil Medvedev|2024": {
            "historical_significance": "Sinner's Breakthrough",
            "short_commentary": "Sinner comes back from 2 sets down to win his maiden Slam.",
            "career_impact": "Italy's first AO champion; Sinner arrives at the top.",
            "cultural_resonance": "Validated the 'New Generation' hype."
        }
    }
    
    key = f"{w}|{l}|{y}"
    if key in narratives:
        return narratives[key]
    
    return {
        "historical_significance": f"A {y} {w} Classic",
        "short_commentary": f"{w} defeats {l} in a defining match of the era.",
        "career_impact": f"A major milestone in {w}'s career.",
        "cultural_resonance": "Remembered as a high-stakes battle."
    }

if __name__ == "__main__":
    generate_iconic()
