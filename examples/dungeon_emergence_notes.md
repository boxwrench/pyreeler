# Dungeon Emergence - Production Notes

## Timing & Pacing Structure (50 seconds)

### Phase 1: Awakening (0-2s) - "P"
- **Visual:** Single @ cursor appears in dark dungeon
- **Audio:** Low drone ambience starts (60Hz)
- **Growth:** Just "P" floating above player
- **Pacing:** Slow, mysterious, establishing shot

### Phase 2: First Growth (2-4s) - "PY"
- **Visual:** Player moves to first room, encounters first enemy
- **Audio:** First impact swell (250Hz), pulse rhythm begins
- **Growth:** Letters stack: P above, PY below
- **Pacing:** Quick reveal, establishing the growth mechanic

### Phase 3: Building Power (4-7s) - "PYR"
- **Visual:** Combat with enemy, defeated enemy fades to 'x'
- **Audio:** Second impact swell (300Hz)
- **Growth:** PYR now visible
- **Pacing:** Action beat, showing game mechanics

### Phase 4: The Journey (7-11s) - "PYRE"
- **Visual:** Player traverses corridors, camera follows smoothly
- **Audio:** Pulse intensifies, ambience thickens
- **Growth:** PYRE floating above like a halo
- **Pacing:** Movement and momentum building

### Phase 5: Near Complete (11-15s) - "PYREE"
- **Visual:** Entering final section of maze
- **Audio:** Higher pitch swell (350Hz), tension building
- **Growth:** Almost there, PYREE glowing brighter
- **Pacing:** Anticipation, approaching climax

### Phase 6: The Reveal (15-20s) - "PYREELER" + VOICE
- **Visual:** Player reaches center, full name materializes
- **Audio:** **VOICE: "Py-Reeler"** with longest swell (400Hz)
- **Growth:** Complete! Full "PYREELER" with bloom/glow effect
- **Pacing:** THE MOMENT - everything converges

### Phase 7: Victory Lap (20-25s) - Hold Full Name
- **Visual:** Full name hovers, player moves freely, enemies defeated
- **Audio:** Pulse triumphant, voice echo fades
- **Pacing:** Celebration, showing completion

### Phase 8: Transition (25-30s)
- **Visual:** Dungeon fades to black, particles begin converging
- **Audio:** All stems fade down
- **Pacing:** Breather before title

### Phase 9: Title Reveal (30-40s)
- **Visual:** Particle explosion converges to form "PYREELER" title
- **Phase 1 (0-3s of this section):** Particles converge from screen edges
- **Phase 2 (3-7s):** Glow builds, title materializes with bloom
- **Phase 3 (7-10s):** "code-generated films" subtitle fades in
- **Pacing:** Epic, satisfying payoff

### Phase 10: Hold (40-50s)
- **Visual:** Clean title card with subtle particle motion
- **Audio:** Just the low drone, sustaining
- **Pacing:** Let it land, final impression

---

## Key Improvements Over Previous Version

### 1. No Debug Text Visible
- All scripting notes removed from final output
- Clean, cinematic presentation

### 2. Growth Completes
- P → PY → PYR → PYRE → PYREE → **PYREELER**
- Each phase has distinct timing (2s, 2s, 3s, 4s, 4s, 5s)
- Progressive difficulty: shorter phases early, longer reveals later

### 3. Voice Integration
- "Py-Reeler" spoken at climax (15s mark)
- Slightly slower rate (-10%) for gravitas
- Audio stems duck under voice for clarity

### 4. Better Dungeon Visualization
- Isometric-style depth with wall highlights
- Fog of war (visibility based on distance from player)
- Floor tiles with subtle noise variation
- Animated enemies (pulsing squares, different types)

### 5. Enemy Representation
- 'E' symbol for enemies (color-coded)
- Two types: 'hunter' (aggressive red), 'patrol' (orange)
- Pulse animation (sinusoidal brightness)
- Death animation: convert to 'x' then fade

### 6. Satisfying Title Reveal
- Particle explosion converging from edges
- Multi-layer glow effect (5 bloom layers)
- "code-generated films" subtitle for context
- Smooth fade-in over 10 seconds (not abrupt)

---

## Technical Notes

### Frame Distribution
```
0-48:    "P"          (2s)
48-96:   "PY"         (2s)  
96-168:  "PYR"        (3s)
168-264: "PYRE"       (4s)
264-360: "PYREE"      (4s)
360-480: "PYREELER"   (5s) <- VOICE HERE
480-600: Hold         (5s)
600-720: Transition   (5s)
720-960: Title reveal (10s)
960-1200: Hold title  (10s)
```

### Audio Stem Mix
- **Ambience:** 60Hz drone, constant throughout
- **Pulse:** 75 BPM heartbeat, represents "life"
- **Impacts:** Pitch rises with each growth phase (250→400Hz)
- **Voice:** "Py-Reeler" at 15s mark, ducked under by other stems

### Visual Polish
- Player glow pulses with sine wave
- Wall highlights give 3D depth
- Fog of war creates mystery/exploration feel
- Camera smoothly follows player (not jarring)

---

## Rendering

```bash
python dungeon_emergence_production.py
```

Output: `dungeon_emergence_output/dungeon_emergence.mp4`

Requirements:
- ffmpeg
- numpy, Pillow
- edge-tts (optional, for voice)
- scipy (optional, for better audio filters)
