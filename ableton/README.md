# Ableton Live Integration

## Overview
Control Ableton Live via Node.js scripts for generating judge music baselines in the Vibe Debating system.

## Setup

### Prerequisites
- Ableton Live 12 Suite (Demo mode acceptable - full MIDI Remote Scripts work)
- Node.js v20+ (for `ableton-js` library)
- MIDI Remote Scripts installed in `~/Music/Ableton/User Library/Remote Scripts/AbletonJS/`

### Installation
```bash
# Install ableton-js library
cd /tmp && npm install ableton-js@4.0.4

# Configure Ableton preferences:
# Preferences → Link/MIDI → Control Surface → select "AbletonJS"
# Restart Ableton after installing scripts
```

## Scripts Location
All MIDI scripts are stored in `/tmp/*.mjs` for easy regeneration per session (Demo mode limitation).

### Available Scripts
| Script | Purpose |
|--------|---------|
| `queqiao-xian-v2.mjs` | 24-bar baseline for Lü Dongbin - Queqiao Xian (G minor, 80 BPM) |
| `clean-play.mjs` | Cleanup/mute old tracks |
| `fire-new.mjs` | Helper to replay scripts |

## Architecture
```
/tmp/*.mjs  →  ableton-js → Ableton Live → Audio Output
      ↓
   Web Audio Capture (Demo mode workaround)
      ↓
   vibe-debating web player
```

## Key Functions
- `browser.loadItem()` - Load E-Piano Rhodish.adg (爵士电钢琴)
- `song.view.set("selected_track", ...)` - Select track before loading
- `song.track.addMIDIClip(...)` - Add melody clips

## Limitations (Demo Mode)
- Cannot save projects - regenerate each session
- Cannot export audio directly - use system audio capture
- 30-day trial period before full lockout

## Next Steps
- Finalize 8 baseline tracks (one per debater)
- Implement audio capture solution for final export
- Integrate with web player via recorded WAV files