from datetime import timedelta, datetime as dt
import re
from py_stealth import *

SKIP_TILE_MESSAGES = [
    "cannot be seen",
    "The fish don't seem",
    "Здесь нет",
    "Пробуй ловить",
    "Далековато"

]
#
NEXT_TRY_MESSAGES = [
    "You fish a while",
    "You pull",
    "Ты поймал"
]

LOOT = [0x175D, 0x1078, 0x0F8E, 0x0F8A, 0x0F78, 0x0F7F, 0x3B03]
HATCH_TYPES = [0x3EAE, 0x3EB9, 0x3E65, 0x3E93]
BANK_WEIGHT_LIMIT = 5300

WATER_TILES = [
    0x00A8, 0x00AB,
    0x0136, 0x0137,
    0x5797, 0x579C,
    0x746E, 0x7485,
    0x7490, 0x74AB,
    0x74B5, 0x75D5
]

def cancel_targets():
    CancelWaitTarget()
    if TargetPresent():
        CancelTarget()

#
def find_hatch() -> int:
    SetFindDistance(3)
    for _hatch in HATCH_TYPES:
        if FindType(_hatch, Ground()):
            _started = dt.now()
            UseObject(FindItem())
            if WaitJournalLine(_started, "stones in your Bank Box", 1000):
                _stones = int(re.search(r"(\d+)", LastJournalMessage()).group())
                if _stones > BANK_WEIGHT_LIMIT:
                    print(f"Bank weight limit reached, current weight {_stones}")
                    SetARStatus(False)
                    Disconnect()

            return LastContainer()

    print("No hatch found, unload to bank disabled")
    return 0


def check_for_loot(hatch: int):
    if hatch > 0:
        for _loot in LOOT:
            if FindType(_loot, Ground()):
                Grab(FindItem(), 0)
                Wait(1000)
                if FindType(_loot, Backpack()):
                    MoveItem(FindItem(), 0, hatch, 0, 0, 0)
                    Wait(1000)

def find_tiles(center_x, center_y, radius):
    _min_x, _min_y = center_x-radius, center_y-radius
    _max_x, _max_y = center_x+radius, center_y+radius
    _tiles_coordinates = GetLandTilesArray(_min_x, _min_y, _max_x, _max_y, WorldNum(), WATER_TILES)
    print("[FindTiles] Found "+str(len(_tiles_coordinates))+" tiles")
    return _tiles_coordinates


def fishing():
    _tiles = find_tiles(GetX(Self()), GetY(Self()), 4)
    for _tile_data in _tiles:
        _tile, _x, _y, _z = _tile_data
        _try = 0
        while not Dead():
            _try += 1
            if _try > 15:
                break

            #
            check_for_loot(find_hatch())
            #
            cancel_targets()
            _started = dt.now()
            UseObject(ObjAtLayer(LhandLayer()))
            WaitForTarget(2000)
            if TargetPresent():
                WaitTargetTile(_tile, _x, _y, _z)
                WaitJournalLine(_started, "|".join(SKIP_TILE_MESSAGES+NEXT_TRY_MESSAGES), 15000)

                if dt.now() >= _started + timedelta(seconds=15):
                    print("WaitJournalLine timeout, bad tile")
                    break

                if InJournalBetweenTimes("|".join(SKIP_TILE_MESSAGES), _started, dt.now()) > 0:
                    break

            else:
                print("continue")
                continue
            Wait(500)

        Wait(500)


def move_boat(direction):
    UOSay("raise anchor")
    Wait(500)
    UOSay(direction)
    Wait(10000)
    UOSay("drop anchor")


SetARStatus(True)
SetWarMode(False)
SetPauseScriptOnDisconnectStatus(True)
while not Dead():
    for _ in range(0, 10):
        fishing()
        move_boat("forward")
    for _ in range(0, 10):
        fishing()
        move_boat("back")
