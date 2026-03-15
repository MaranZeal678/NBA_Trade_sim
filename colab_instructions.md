# How to Run NBA Trade Simulator in Google Colab

This system is designed to be modular and run in a standard Python environment.

## Steps

1. **Prepare the Files**
   - Zip the entire `Sim` folder (or just the `src` folder and `run_simulation.py`).

2. **Upload to Colab**
   - Open a new Notebook.
   - Click the "Files" icon on the left sidebar.
   - Upload your `Sim.zip`.

3. **Unzip and Setup**
   Run the following cell to unzip and set up the path:
   ```python
   !unzip Sim.zip
   %cd Sim
   ```

4. **Run the Simulation**
   Execute the runner script:
   ```python
   !python run_simulation.py
   ```

## Expected Output
You will see:
1. **Projected Standings**: A list of all 30 teams with their W-L record and Strategy (Buyer/Seller).
2. **Trade Proposals**: A ranked list of the ~5-10 best trades found by the engine, including:
   - Full player packages.
   - Detailed Salary Math (proving CBA compliance).
   - Strategic Rationale.

## Customization
To change the simulation context (e.g., make the Lakers a Seller), edit `run_simulation.py` or `src/sim/engine.py`.
