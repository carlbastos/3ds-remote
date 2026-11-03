# Agents: operating the 3DS

This repo exists so an AI agent can use a real Nintendo 3DS: see its screens, press its buttons,
install and launch software. Start with [`.claude/skills/3ds-control/SKILL.md`](.claude/skills/3ds-control/SKILL.md),
which covers:

- what has to be running on the console (3DS Remote, NTR-HR, Rosalina InputRedirection) and how
  to check each one;
- the control loop: `3ds snap`, one action, wait, `3ds snap` again;
- what never to do (backlights off through `gsp::Lcd`, NTR's old remote-play format);
- references for the [HOME Menu](.claude/skills/3ds-control/references/home-menu.md),
  [installing and downgrading](.claude/skills/3ds-control/references/installing.md) and
  [recovery](.claude/skills/3ds-control/references/recovery.md).

Working on the code itself: see [README.md](README.md#build) for building, releasing and the API.
