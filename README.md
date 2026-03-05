### Here are the exact steps to run both servers (MCP Server + Orchestrator) and test the PPE workflow end-to-end.
##These steps assume:
##You are inside the project root folder (edge_ai_orchestrator/)
##You have Python 3.10+ installed
##You added the files exactly as per the skeleton

#STEP 1 — Create and Activate Virtual Environment
python -m venv venv
source venv/bin/activate

#STEP 2 — Install Dependencies
pip install -r requirements.txt

#STEP 3 — Run the MCP SERVER (Port 8001)
uvicorn mcp_server.main:app --reload --port 8001

#STEP 4 — Run the ORCHESTRATOR API (Port 8000)
Open a second terminal (or VS Code new terminal tab):

Activate virtual environment again if needed:
source venv/bin/activate
uvicorn orchestrator.api.main:app --reload --port 8000

#STEP 5 — Run the API Server (Port 8015)
Open a third terminal (or VS Code new terminal tab):

Activate virtual environment again if needed:
source venv/bin/activate
cd api
uvicorn app.main:app --reload --host 0.0.0.0 --port 8015

#STEP 6 — Run the WebApp Server
Open a third terminal (or VS Code new terminal tab):

cd webapp
npm install
npm run dev