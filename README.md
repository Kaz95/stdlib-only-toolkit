# stdlib-only-toolkit

Shared code and per-assignment submissions for a semester of terminal-based
Python coursework. Every assignment in this class has the same constraint:
the graded submission has to be a single .py file, and it can only use the
standard library. No pip packages, no splitting logic across multiple files
in the actual handed-in code.

Since most of these projects end up needing the same handful of things
(bordered terminal UI, bitmap rendering, audio playback), this repo keeps a
reusable version of that code in one place, separate from the flattened,
single-file versions that actually get submitted.

## Layout

```
toolkit/     reusable modules, written and organized normally
assets/      source media and the generated data pulled from at runtime
projects/    the actual per-assignment submissions
```

### toolkit/

- `canvas.py` - ANSI color and cursor-control constants, bordered box
  drawing, and a small bitmap font renderer built from hand-encoded 4-bit
  sprite data. The `Drawing.draw_window` method currently still contains
  the tip calculator's specific layout. That's being pulled out so this
  file only holds a generic bordered box primitive, with per-project UI
  layered on top elsewhere.
- `animator.py` - fades a bitmap in and out in the terminal using linear
  interpolation between colors, frame by frame, written directly with
  24-bit ANSI escape codes.
- `audio.py` - strips a WAV file down to its raw PCM bytes, and rebuilds a
  playable WAV in memory from those bytes at runtime using only `wave` and
  `winsound`. Playback runs on a background thread so it doesn't block.
- `assets_prep.py` - a dev-only script for downscaling source images into
  a JSON pixel matrix. This is the one file in the repo that uses a
  third-party library (Pillow), which is fine because it never gets
  shipped as part of a graded submission. It's a one-time prep step, not
  runtime code.

### assets/

- `source_images/`, `source_audio/` - original media before processing.
- `generated/` - the output of the prep scripts (`panera_logo_bitmap.json`,
  `kaching_audio_bytes`). These files are also fetched directly over HTTP
  at runtime by the submitted projects, which is how a single-file
  submission can still ship a bitmap image and a sound effect without
  bundling any binary data in the file itself.

### projects/

Each assignment's actual submission. These are hand-flattened right now:
whatever a project needs from `toolkit/` gets copied and inlined directly
into the submitted file, since there's no automated way yet to pull just
the needed pieces into one file. That means the `toolkit/` version and the
copy living inside a given project's submission can drift out of sync. A small 
script to handle that assembly step automatically is a likely future addition, 
but not something this repo does yet.

## Known issues

- Animator is too slow.
   
  - I'm working on implementing pre-rendered interpolated fade. Separating the frame rendering from the sleep/framerate
    should help a lot. I might use this as a tool to learn profiling and optimization in Python, since I don't have a 
    lot of experience with that yet.`Update: Prototype implemented`.

  - I'm also looking into doing precomputed color runs during the pre-rendering step. This would fix the issue 
    of sending a new ANSI color code for every pixel in every frame, which is a lot of overhead. 
    Instead, I could send a single color code per run of pixels, which would be a lot more efficient. 