# FM Synthesis Notes

Initial experiments with FM synthesis module.

## Observations

Bell tones at 440Hz with index=2.0 sound convincingly like chimes.
Brass tones need more work - the envelope is more important than the ratio.
Woodwind sounds surprisingly good with 3:1 ratio.

## Parameter Sweet Spots

- Bell: 1:1 ratio, index 2-4, fast attack, no sustain, long release
- Brass: 2:1 ratio, index 4-6, medium attack, high sustain
- Woodwind: 3:1 or 3:2 ratio, index 1-2, slow attack
- Metallic: 1:1 or 1:2 ratio, high index (5+), any envelope

## Issues

- Higher indices get noisy quickly
- Need band limiting for frequencies above Nyquist
- Multiple operators would open up more possibilities

## Next Steps

- Try cascading 3+ operators
- Add pitch envelope for percussive attacks
- Explore feedback FM (operator modulates itself)
