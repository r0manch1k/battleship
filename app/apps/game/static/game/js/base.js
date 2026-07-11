const fleet = [4, 3, 3, 2, 2, 2, 1, 1, 1, 1];
const boardSize = 10;

function samePoint(a, b) {
  return a.x === b.x && a.y === b.y;
}

function inside(point) {
  return (
    point.x >= 0 && point.x < boardSize && point.y >= 0 && point.y < boardSize
  );
}

function shipCells(ship) {
  return Array.from({ length: ship.length }, (_, index) => ({
    x: ship.orientation === 'H' ? ship.x + index : ship.x,
    y: ship.orientation === 'V' ? ship.y + index : ship.y,
  }));
}

function neighbors(point) {
  const result = [];
  for (let dx = -1; dx <= 1; dx += 1) {
    for (let dy = -1; dy <= 1; dy += 1) {
      const neighbor = { x: point.x + dx, y: point.y + dy };
      if (inside(neighbor)) {
        result.push(neighbor);
      }
    }
  }
  return result;
}

function canPlace(ships, nextShip) {
  const cells = shipCells(nextShip);
  if (cells.some((cell) => !inside(cell))) {
    return false;
  }

  const blocked = ships.flatMap((ship) => shipCells(ship).flatMap(neighbors));
  return !cells.some((cell) =>
    blocked.some((blockedCell) => samePoint(cell, blockedCell))
  );
}

function setupPlacement() {
  const board = document.querySelector('#placement-board');
  const form = document.querySelector('#placement-form');
  if (!board || !form) {
    return;
  }

  const lengthSelect = document.querySelector('#ship-length');
  const orientationSelect = document.querySelector('#ship-orientation');
  const shipsInput = document.querySelector('#ships-input');
  const count = document.querySelector('#placement-count');
  const reset = document.querySelector('#reset-placement');
  const ships = [];

  function updateControls() {
    board.querySelectorAll('.cell').forEach((cell) => {
      cell.classList.remove('cell_ship');
    });

    ships.forEach((ship) => {
      shipCells(ship).forEach((point) => {
        const cell = board.querySelector(
          `[data-x="${point.x}"][data-y="${point.y}"]`
        );
        if (cell) {
          cell.classList.add('cell_ship');
        }
      });
    });

    shipsInput.value = JSON.stringify(ships);
    count.textContent = `Placed: ${ships.length} of ${fleet.length}`;

    const remaining = [...fleet];
    ships.forEach((ship) => {
      const index = remaining.indexOf(ship.length);
      if (index >= 0) {
        remaining.splice(index, 1);
      }
    });

    lengthSelect.innerHTML = '';
    remaining.forEach((length) => {
      const option = document.createElement('option');
      option.value = length;
      option.textContent = `${length} cells`;
      lengthSelect.append(option);
    });
  }

  board.addEventListener('click', (event) => {
    const cell = event.target.closest('.cell');
    if (!cell || ships.length >= fleet.length || !lengthSelect.value) {
      return;
    }

    const nextShip = {
      length: Number(lengthSelect.value),
      x: Number(cell.dataset.x),
      y: Number(cell.dataset.y),
      orientation: orientationSelect.value,
    };

    if (!canPlace(ships, nextShip)) {
      cell.animate(
        [
          { transform: 'scale(1)' },
          { transform: 'scale(0.9)' },
          { transform: 'scale(1)' },
        ],
        { duration: 150 }
      );
      return;
    }

    ships.push(nextShip);
    updateControls();
  });

  reset.addEventListener('click', () => {
    ships.splice(0, ships.length);
    updateControls();
  });

  form.addEventListener('submit', (event) => {
    if (ships.length !== fleet.length) {
      event.preventDefault();
      count.textContent = 'Place all 10 ships first';
    }
  });

  updateControls();
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', setupPlacement);
} else {
  setupPlacement();
}
