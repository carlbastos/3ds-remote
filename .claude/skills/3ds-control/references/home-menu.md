# HOME Menu

Coordinates below are bottom-screen pixels (subtract 40/240 from a `snap` image). They come
from a New 3DS XL with the default 4-row icon size; re-check with a snap before relying on them.

## Layout

- Bottom screen: a grid of icons, 4 rows, scrolled horizontally. Row centres are roughly
  y = 62, 108, 150, 190. The top bar (y < 40) holds the system applets (Settings, notes, Miiverse, …).
- Bottom bar: `Settings` / `Manual` on the left, `Open` (or `Resume`) on the right. With software
  suspended it shows `Close` at about (53, 227).
- Top screen: banner of the selected icon. A folder shows a blue folder with its name.
- Scroll the grid with a fast swipe: `3ds drag 280,150 40,150 --grab 50 --move 300 --drop 50`
  goes right (towards the empty end); swap the x values to go left. The game card and the first
  installed titles sit at the far left.

## Selecting and opening

- `touch` an icon once to select it (banner appears), then `press A` (or touch it again) to open.
- A folder opens as a panel over the grid with up to 7 columns x 3 rows of icons; its **back tab**
  (arrow) is at about (57, 55). `press B` closes it.

## Moving icons

`drag` waypoints are what make this reliable: hold ~2 s to lift the icon, then move.

- **Into a folder:** carry the icon over the folder icon and hold there ~4-5 s until the folder
  opens, then move to an **empty** slot inside and release. Releasing on the closed folder icon
  snaps the icon back to where it was.
  `3ds drag <icon x,y>:2200 <folder x,y>:4800 <empty slot inside>:1200`
- **Out of a folder:** carry it to the back tab and hold ~3 s until the folder closes, then move to
  an empty grid slot and release.
  `3ds drag <icon x,y>:2200 57,55:3200 <empty slot>:1000`
- **Swap trap:** releasing on an **occupied** grid slot swaps the two icons. When the dragged icon
  came from a folder, the displaced icon is moved **into that folder**, in the dragged icon's old
  place. If that happens, drag the displaced icon back out to the now-empty slot.
- Empty slots show a small grey square. After a move, snap again and compare with the layout from
  before; put back anything you displaced.

## Software

- Launch: select the icon, `press A`. Games may show a first-run dialog (e.g. StreetPass); `A`
  dismisses it.
- Suspend: `press HOME`. The top screen then shows "Suspended Software" and the bottom bar shows
  `Close` / `Resume`.
- Close: `press HOME`, wait ~3 s, `touch 53 227` (Close), then `press A` on "Would you like to close
  this software?". Unsaved progress is lost.
- Only one application runs at a time: launching another title (or `3ds launch`) closes the
  current one, including 3DS Remote.
