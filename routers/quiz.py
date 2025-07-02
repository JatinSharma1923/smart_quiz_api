from fastapi import APIRouter
router = APIRouter()

@router.get('/generate')
def generate():
    return {'message': 'Quiz generator coming soon'}
