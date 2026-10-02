from fastapi import APIRouter, HTTPException, status

router = APIRouter()

data_table = []

@router.get("/data", status_code=status.HTTP_200_OK)
async def get_data():
    return {"data": data_table}

@router.post("/data", status_code=status.HTTP_201_CREATED)
async def get_data(data : str):
    if data in data_table:
        raise HTTPException(status_code=400, detail="Data already exists")
    data_table.append(data)
    return {"message": data}
