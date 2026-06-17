from fastapi import APIRouter, Depends, HTTPException, status, Response, Form
# from sqlalchemy.orm import Session
# from app.core.database import get_db
# from app.core.security import verify_password, create_access_token

router = APIRouter()

@router.post("/login")
async def login(
        response: Response,
        email: str = Form(...),
        password: str = Form(...)
        # db: Session = Depends(get_db) # Quitar comentario al conectar la BD real
):
    """
    Procesa el login, inyecta la cookie JWT y devuelve JSON si es exitoso.
    """
    # Logica temporal de demostración:
    if email != "admin@unison.mx" or password != "modd2026":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales incorrectas"
        )

    # Simulación de token (aquí va la logica de security.py)
    fake_token = "eyJHBGciOiJUzI1NiIsInR5cCI..."

    response.set_cookie(
        key="access_token",
        value=f"Bearer {fake_token}",
        httponly=True,
        samesite="lax"
    )

    # Devolvemos JSON puro para que el JS del frontend decia qué hacer
    return {"message": "Autenticación exitosa", "user": email, "redirect": "/dashboard"}
