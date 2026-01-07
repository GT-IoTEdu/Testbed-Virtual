from pydantic import BaseModel, IPvAnyAddress, Field

class DeviceCreate(BaseModel):
    """
    Modelo Pydantic para cadastro de dispositivos IoT.
    Utilizado nos endpoints de cadastro e listagem de dispositivos.
    
    Campos:
        ip (IPvAnyAddress): Endereço IP do dispositivo.
        mac (str): Endereço MAC do dispositivo (validação por pattern).
        description (str): Descrição do dispositivo.
    """
    ip: IPvAnyAddress
    mac: str = Field(..., pattern=r'^([0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}$')
    description: str

    class Config:
        schema_extra = {
            "example": {
                "ip": "192.168.10.50",
                "mac": "00:1A:2B:3C:4D:5E",
                "description": "Sensor Ambiental - Lab 5A"
            }
        } 