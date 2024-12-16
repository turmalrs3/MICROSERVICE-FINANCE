# API
from fastapi import FastAPI
import uvicorn
# Requests
import asyncio
import httpx
# DATABASE
from sqlalchemy import create_engine
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
# Classes
from pydantic import BaseModel
from datetime import datetime, date
from typing import List

DB_INFO = "mysql+pymysql://admin:turmalrs1234@terraform-20241129194814887300000007.chye8488mdam.us-east-1.rds.amazonaws.com:3306/saudeplusdb"

engine = create_engine(DB_INFO, echo=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
# ALTERAR AQUI NO FINAL
app = FastAPI(root_path="/service2")

# Dentro dos appointments ao criar:
# Receber lista de treatment ids
# Loop inserir em AppointmentTreatment
# (Inserir total no finance detail na criacao de um appointment)
#
#
# Procurar tratamentos em AppointmentTreatment where id = appointment_id
# Procurar cost para cada treatment em Treatment
# Calcular total
# 
# Verificar data due em FinanceDetail para appointment id
# Enviar lista de treatment necessary (com o seu custo individual?)
# Procurar o healthinsurance do paciente e retornar qual e a %
# Calcular percentagem de desconto e retornar tudo

# Gets:
# AppointmentTreatment where id = appointment_id (get todos os tratamentos)
# Treatment where id = treatment_id (name e cost para cada um)
# Appointment where appointment_id (get user id)
# Patient where id (get insurance id)
# Insurance where insurance id (name e %)

# Resposta: Appointment Date, Treatment list, health insurance, % insurance, total com o desconto

# Get Finance By Appointment
@app.get("/finance/{appointment_id}", tags=["Finance"])
async def get_finance_details(appointment_id: int):
    db_session = SessionLocal()

    try:
        query = """
        SELECT 
            a.AppointmentID,
            a.AppointmentDateTime,
            p.PatientID,
            COALESCE(SUM(t.Cost), 0) AS TotalTreatmentCost,
            s.Price AS SpecialityCost,
            COALESCE(SUM(t.Cost), 0) + s.Price AS TotalConsultationCost,
            h.InsuranceDiscount,
            h.InsuranceCompany,
            ROUND((COALESCE(SUM(t.Cost), 0) + s.Price) * (1 - COALESCE(h.InsuranceDiscount, 0) / 100), 2) AS FinalCostWithInsurance
        FROM 
            Appointment a
        JOIN 
            Patient p ON a.PatientID = p.PatientID
        LEFT JOIN 
            HealthInsurance h ON p.HealthInsuranceID = h.HealthInsuranceID
        JOIN 
            Doctor d ON a.DoctorID = d.DoctorID
        JOIN 
            Speciality s ON d.SpecialityID = s.SpecialityID
        LEFT JOIN 
            AppointmentTreatment at ON a.AppointmentID = at.AppointmentID
        LEFT JOIN 
            Treatment t ON at.TreatmentID = t.TreatmentID
        WHERE
            a.AppointmentID = :appointment_id
        GROUP BY 
            a.AppointmentID, p.PatientID, s.Price, h.InsuranceDiscount;
        """

        # Execute the query with the appointment_id parameter
        result = db_session.execute(text(query), {"appointment_id": appointment_id})
        finance_details = result.fetchone()

        result = db_session.execute(text(f"SELECT * FROM AppointmentTreatment WHERE AppointmentID = {appointment_id}"))
        treatments = result.fetchall()

        if finance_details:
            finance_dict = finance_details#dict(finance_details)
            return {"status": "success", "data": finance_dict, "treatments": treatments}
        
        else:
            return {"status": "error", "message": "Appointment not found."}

    except Exception as e:
        return {"status": "error", "message": f"Error retrieving finance details: {str(e)}"}


# CREATE FinanceDetail
@app.post("/finance_detail", tags=["Finance"])
async def finance_detail(appointment_id: int):
    db_session = SessionLocal()
    # get todos os tratamentos
    # get insurance
    # calcular total
    # criar

    try:

        result = db_session.execute(text(f"SELECT * FROM AppointmentTreatment WHERE AppointmentID = {appointment_id}"))
        results = result.fetchall()

        totalcost = 0

        for item in results:
            treatment = db_session.execute(text(f"SELECT * FROM Treatment WHERE TreatmentID = {item[2]}")) # Treatment ID
            treatment_info = treatment.fetchone()
            totalcost += treatment_info[2]

        result = db_session.execute(text(f"SELECT * FROM Appointment WHERE AppointmentID = {appointment_id}"))
        results = result.fetchone()

        patient_id = results[1]

        result = db_session.execute(text(f"SELECT * FROM Patient WHERE PatientID = {patient_id}"))
        results = result.fetchone()

        insurance_id = results[7]

        result = db_session.execute(text(f"SELECT * FROM HealthInsurance WHERE HealthInsuranceID = {insurance_id}"))
        results = result.fetchone()

        discount = results[2]

        final_price = totalcost-((discount/100)*totalcost) # ADICIONAR CONSULTA (SPECIALITY)
    
        db_session.execute(text("INSERT INTO FinanceDetail (SubTotal, AppointmentID, PaymentStatusID) VALUES (:SubTotal, :AppointmentID, :PaymentStatusID)"),
        {
            "SubTotal": final_price,
            "AppointmentID": appointment_id,
            "PaymentStatusID": 1 })
        
        db_session.commit()

        return {"status": "success", "data": "Finance Detail created."}

    except:
        return {"status": "error", "data": "Error"}

        
# Start service
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8002)
