cd omnicore-ui
start cmd /k npm run dev

cd ../backend
start cmd /k uvicorn main:app --reload --port 8000
