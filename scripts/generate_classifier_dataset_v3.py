from pathlib import Path
from datetime import date, timedelta
import csv
import random
import re

# Dataset V3: 1,600 synthetic examples, with template-family-disjoint splits.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = PROJECT_ROOT / "data" / "synthetic_data"
OUTPUT_FILE = OUTPUT_DIR / "classifier_dataset_v3.csv"
SEED = 73
rng = random.Random(SEED)

LABELS = ["admission_advice", "discharge_summary", "hospital_bill", "signed_claim_form"]
SPLITS = {
    "train": {"templates": range(0, 8), "count": 300},
    "validation": {"templates": range(8, 10), "count": 50},
    "test": {"templates": range(10, 13), "count": 25},
    "challenge": {"templates": range(13, 16), "count": 25},
}

PATIENTS = ["Aarav Sharma", "Riya Patel", "Kabir Mehta", "Ananya Verma", "Ishaan Gupta", "Meera Nair", "Vivaan Rao", "Sara Khan", "Arjun Malhotra", "Diya Iyer", "Reyansh Shah", "Aditi Joshi", "Jonathan Reed", "Maya Thomas", "Nikhil Das", "Priya Menon"]
HOSPITALS = ["Green Valley Hospital", "City Care Medical Centre", "Sunrise Multispeciality Hospital", "Hopewell Hospital", "Metro Health Centre", "National Medical Institute", "Silverline Hospital", "City General Hospital"]
DOCTORS = ["Dr. Amit Shah", "Dr. Neha Kapoor", "Dr. Rahul Nair", "Dr. Priya Mehta", "Dr. Karan Rao", "Dr. Anjali Verma", "Dr. Sarah Chen", "Dr. Michael Lewis"]
DIAGNOSES = ["acute respiratory infection", "gastrointestinal infection", "viral fever", "dehydration", "post-operative recovery", "acute abdominal pain", "urinary tract infection", "community acquired pneumonia", "cholecystitis", "renal calculus"]
TREATMENTS = ["medication and clinical observation", "intravenous fluids and medication", "antibiotic therapy", "surgical treatment and monitoring", "supportive care and observation", "diagnostic tests and medical management", "pain management and follow-up monitoring"]
DEPARTMENTS = ["General Medicine", "Cardiology", "Orthopaedics", "General Surgery", "Neurology", "Emergency Medicine", "Paediatrics", "Urology"]
FOLLOWUPS = ["Review after seven days", "Continue prescribed medicines", "Attend the outpatient department", "Return for clinical assessment", "Follow up with the treating consultant"]
INSURERS = ["Northstar Health Assurance", "Everwell Insurance Services", "Pioneer Medical Cover", "Summit Health Protection"]
CLAIM_TYPES = ["Cashless Hospitalization", "Medical Reimbursement", "Inpatient Treatment", "Hospitalization Expenses"]
PAYMENT = ["Paid", "Partially Paid", "Pending", "Settled"]


def make_values():
    start = date(2024, 1, 1)
    adm = start + timedelta(days=rng.randint(0, 900))
    dis = adm + timedelta(days=rng.randint(1, 14))
    room = rng.randrange(5000, 35001, 500)
    doctor_fee = rng.randrange(1000, 10001, 500)
    medicine = rng.randrange(1000, 18001, 500)
    procedure = rng.randrange(0, 25001, 500)
    lab = rng.randrange(500, 8001, 500)
    subtotal = room + doctor_fee + medicine + procedure + lab
    tax = round(subtotal * 0.05 / 10) * 10
    total = subtotal + tax
    paid = rng.choice([total, max(0, total - rng.randrange(1000, 10001, 500))])
    return {
        "patient": rng.choice(PATIENTS), "hospital": rng.choice(HOSPITALS),
        "doctor": rng.choice(DOCTORS), "claim": f"CLM{rng.randint(1,99999):05d}",
        "policy": f"POL{rng.randint(1,999999):06d}", "insurer": rng.choice(INSURERS),
        "admission": adm.strftime("%d/%m/%Y"), "discharge": dis.strftime("%d/%m/%Y"),
        "signed": (adm + timedelta(days=rng.randint(0, 5))).strftime("%d/%m/%Y"),
        "dob": (start - timedelta(days=rng.randint(7000, 24000))).strftime("%d/%m/%Y"),
        "diagnosis": rng.choice(DIAGNOSES), "treatment": rng.choice(TREATMENTS),
        "department": rng.choice(DEPARTMENTS), "followup": rng.choice(FOLLOWUPS),
        "claim_type": rng.choice(CLAIM_TYPES), "payment": rng.choice(PAYMENT),
        "room": room, "doctor_fee": doctor_fee, "medicine": medicine,
        "procedure": procedure, "lab": lab, "subtotal": subtotal, "tax": tax,
        "total": total, "paid": paid, "balance": total-paid,
        "days": (dis-adm).days, "ward": rng.choice(["Ward 2A - Bed 08", "Ward 4B - Bed 12", "ICU - Bed 03", "Ward 5C - Bed 17"]),
        "phone": f"9{rng.randint(100000000,999999999)}", "city": rng.choice(["Pune", "Mumbai", "Bengaluru", "Hyderabad", "Chennai", "Delhi"]),
    }

# Each list contains 16 different document formats. Split assignment below
# keeps every template family exclusive to one split.
T = {
"admission_advice": [
"HOSPITAL ADMISSION ADVICE\nPATIENT INFORMATION\nPatient Full Name: {patient}\nDate of Birth: {dob}\nPatient Reference: {claim}\nHospital: {hospital}\nADMISSION DETAILS\nDate of Admission: {admission}\nDepartment: {department}\nAssigned Ward / Bed: {ward}\nAdmitting Physician: {doctor}\nCLINICAL SUMMARY\nProvisional Diagnosis: {diagnosis}\nThe patient is advised to report to the admission desk for inpatient registration.\nPRE-ADMISSION INSTRUCTIONS\nBring identification, insurance card and current medication list.\nPatient / Representative: {patient}",
"EMERGENCY INPATIENT ADMISSION NOTICE\nFacility: {hospital}\nPatient: {patient}\nEmergency Reference: {claim}\nRegistration Date: {admission}\nReceiving Unit: {department}\nConsultant on Call: {doctor}\nInitial Assessment: {diagnosis}\nAdmission Decision: Admit for inpatient evaluation and treatment.\nWard Allocation: {ward}\nPlease complete admission formalities at the emergency registration counter.",
"INPATIENT REGISTRATION FORM\nSECTION A - PATIENT DETAILS\nName: {patient}\nDate of Birth: {dob}\nMedical Record Number: {claim}\nSECTION B - ADMISSION RECORD\nHospital: {hospital}\nAdmission Date: {admission}\nDepartment: {department}\nBed Assignment: {ward}\nTreating Consultant: {doctor}\nSECTION C - REASON FOR ADMISSION\nProvisional Diagnosis: {diagnosis}\nRegistration Status: Patient admitted for hospital treatment.",
"NOTICE OF PLANNED HOSPITALIZATION\nTo: {patient}\nHealthcare Provider: {hospital}\nAuthorization Reference: {claim}\nProposed Admission Date: {admission}\nRequested Specialty: {department}\nConsulting Doctor: {doctor}\nClinical Reason: {diagnosis}\nPlease present this notice at the admissions office with photo identification and policy card.\nHospital Admissions Department",
"PATIENT ADMISSION AUTHORIZATION\nAuthorization Number: {claim}\nHospital Name: {hospital}\nPatient Name: {patient}\nPolicy Number: {policy}\nAdmission Date: {admission}\nAdmission Type: Emergency\nDepartment: {department}\nAttending Physician: {doctor}\nReason for Admission: {diagnosis}\nAuthorization Status: Admission recorded. This is not a final bill.",
"HOSPITAL ADMISSION INTAKE\nRegistration Details\nPatient Name: {patient}\nMedical Record Number: {claim}\nDate of Birth: {dob}\nContact: {phone}\nAdmission Details\nDate: {admission}\nUnit: {department}\nBed Assignment: {ward}\nPrimary Doctor: {doctor}\nClinical Note: Patient referred for assessment of {diagnosis}.\nDisposition: Admit for observation and management.",
"INPATIENT ADMISSION COMMUNICATION\nFrom: Patient Services, {hospital}\nRegarding: Admission of {patient}\nReference ID: {claim}\nDate of Entry: {admission}\nService Line: {department}\nResponsible Consultant: {doctor}\nAdmission Indication: {diagnosis}\nThe hospital confirms that the patient has been accepted into the inpatient service.\nDestination: {ward}",
"ADMISSION ADVICE AND PATIENT DIRECTIVES\nHospital: {hospital}\nPatient / Insured Member: {patient}\nCase Reference: {claim}\nAdmission Date: {admission}\nAdmitting Department: {department}\nConsultant: {doctor}\nProvisional Diagnosis: {diagnosis}\nInstructions: Report to registration, carry identification and insurance details, bring current medicines, and follow fasting directions from the clinical team.\nAdmission Location: {ward}",
"PATIENT ARRIVAL AND ADMISSION RECORD\nFacility Name: {hospital}\nPatient Identifier: {claim}\nPatient: {patient}\nArrival Date: {admission}\nTriage Department: {department}\nAdmission Disposition: Inpatient admission\nClinical Impression: {diagnosis}\nAdmitting Clinician: {doctor}\nThe patient is being transferred from assessment to an inpatient bed: {ward}.",
"HOSPITAL BED ALLOCATION ADVICE\nPatient: {patient}\nHospital: {hospital}\nAdmission Reference: {claim}\nDate of Admission: {admission}\nWard / Room: {ward}\nSpecialty: {department}\nConsultant in Charge: {doctor}\nReason for Hospitalization: {diagnosis}\nBed Status: Allocated. Please contact the inpatient desk for admission formalities.",
"ADMISSION ORDER\nOrder Number: {claim}\nPatient Name: {patient}\nFacility: {hospital}\nOrder Date: {admission}\nAdmit Under: {doctor}\nDepartment: {department}\nWorking Diagnosis: {diagnosis}\nLevel of Care: Inpatient\nThe patient is directed to be admitted for further clinical evaluation.\nWard requested: {ward}",
"INPATIENT ADMISSION CHECKLIST\nHospital: {hospital}\nPatient Name: {patient}\nMedical Reference: {claim}\nAdmission Date: {admission}\nDepartment: {department}\nConsultant: {doctor}\nReason: {diagnosis}\nIdentity verification: Pending / completed\nInsurance details: To be collected\nWard allocation: {ward}\nAdmission status: Registered for inpatient care.",
"ADMISSION INTIMATION TO INSURER\nInsurer: {insurer}\nMember Name: {patient}\nPolicy Number: {policy}\nClaim Reference: {claim}\nHospital: {hospital}\nDate of Admission: {admission}\nDepartment: {department}\nProvisional Diagnosis: {diagnosis}\nAttending Doctor: {doctor}\nThis intimation reports commencement of an inpatient hospitalization.",
"HOSPITALIZATION ENTRY FORM\nPatient Particulars\nName: {patient}\nDOB: {dob}\nMRN: {claim}\nFacility: {hospital}\nAdmission Date: {admission}\nWard: {ward}\nDepartment: {department}\nProvisional Diagnosis: {diagnosis}\nMedical Officer: {doctor}\nEntry Status: Admitted\nPurpose: Record the patient's admission into hospital care.",
"DAY OF ADMISSION INSTRUCTIONS\nDear {patient}, your admission at {hospital} is recorded for {admission}.\nAdmission Reference: {claim}\nDepartment: {department}\nConsultant: {doctor}\nReason for Admission: {diagnosis}\nPlease arrive at the registration counter and proceed to {ward}. Carry your policy card, identity document and relevant medical reports.\nInpatient Admissions Team",
"TRANSFER TO INPATIENT SERVICE\nPatient: {patient}\nHospital Record: {claim}\nFacility: {hospital}\nTransfer Date: {admission}\nTransferred To: {department}\nBed: {ward}\nAdmitting Doctor: {doctor}\nAssessment: {diagnosis}\nTransfer Decision: Admit for continued inpatient management. The receiving ward should complete admission documentation.",
],
"discharge_summary": [
"FINAL HOSPITAL DISCHARGE SUMMARY\nPatient Name: {patient}\nMedical Record: {claim}\nHospital: {hospital}\nDate of Admission: {admission}\nDate of Discharge: {discharge}\nFINAL DIAGNOSIS\n{diagnosis}\nCLINICAL COURSE\nThe patient received {treatment} during the hospital stay.\nCondition at Discharge: Stable\nDischarge Medication: Continue medicines as prescribed.\nFollow-up Plan: {followup}\nConsultant: {doctor}",
"INPATIENT DISCHARGE REPORT\nFacility: {hospital}\nPatient: {patient}\nCase Reference: {claim}\nLength of Stay: {days} days\nAdmission: {admission}\nDischarge: {discharge}\nPresenting Diagnosis: {diagnosis}\nTreatment and Procedures: {treatment}\nHospital Course: The patient was monitored and responded to the treatment plan.\nStatus on Release: Stable\nReview Appointment: {followup}\nDischarging Physician: {doctor}",
"CLINICAL DISCHARGE NOTE\nPatient Details: {patient}\nHospital Number: {claim}\nProvider: {hospital}\nAdmitted On: {admission}\nReleased On: {discharge}\nPrincipal Diagnosis: {diagnosis}\nInvestigations and Treatment: {treatment}\nClinical Findings at Discharge: Stable.\nMedication Advice: Take medication according to prescription.\nFollow-up Instructions: {followup}\nAttending Consultant: {doctor}",
"SUMMARY OF PATIENT HOSPITALIZATION\nName: {patient}\nReference: {claim}\nHospital Name: {hospital}\nInpatient Period: {admission} to {discharge}\nReason for Admission: {diagnosis}\nManagement During Stay: {treatment}\nOutcome: Treatment completed and patient discharged.\nCondition: Stable\nNext Clinical Review: {followup}\nTreating Doctor: {doctor}",
"POST-OPERATIVE DISCHARGE RECORD\nPatient: {patient}\nCase ID: {claim}\nHospital: {hospital}\nAdmission Date: {admission}\nDischarge Date: {discharge}\nFinal Clinical Diagnosis: {diagnosis}\nProcedure / Treatment Summary: {treatment}\nRecovery Notes: Patient observed after treatment and considered stable.\nDischarge Status: Released to home care.\nHome Care Advice: {followup}\nSurgeon / Consultant: {doctor}",
"DISCHARGE MEDICAL CERTIFICATE\nThis certifies that {patient}, reference {claim}, was treated at {hospital}.\nDate of Admission: {admission}\nDate of Discharge: {discharge}\nDiagnosis on Discharge: {diagnosis}\nTreatment Administered: {treatment}\nCondition at discharge: Stable.\nThe inpatient episode has concluded.\nFollow-up: {followup}\nMedical Officer: {doctor}",
"FINAL INPATIENT CARE REPORT\nPatient Name: {patient}\nFacility: {hospital}\nClaim Reference: {claim}\nAdmission Date: {admission}\nRelease Date: {discharge}\nPrincipal Problem: {diagnosis}\nCare Provided: {treatment}\nClinical Outcome: Improved and stable.\nDischarge Destination: Home\nAdvice on Discharge: {followup}\nConsultant in Charge: {doctor}",
"DISCHARGE INSTRUCTIONS AND SUMMARY\nPatient: {patient}\nHospital: {hospital}\nPatient Reference: {claim}\nHospitalized From: {admission}\nDischarged On: {discharge}\nFinal Diagnosis: {diagnosis}\nTreatment Course: {treatment}\nAt discharge the patient was clinically stable.\nMedication and Diet: Follow the prescription.\nNext Appointment: {followup}\nAuthorized By: {doctor}",
"CONTINUITY OF CARE - DISCHARGE SUMMARY\nPatient Identifier: {claim}\nPatient Name: {patient}\nHospital / Facility: {hospital}\nAdmission: {admission}\nDischarge: {discharge}\nDischarge Diagnosis: {diagnosis}\nSummary of Care: {treatment}\nStatus at Release: Stable\nOngoing Care Requirements: {followup}\nResponsible Clinician: {doctor}",
"PATIENT RELEASE SUMMARY\nName of Patient: {patient}\nMedical Case Number: {claim}\nInstitution: {hospital}\nDates of Stay: {admission} - {discharge}\nFinal Assessment: {diagnosis}\nTherapy Delivered: {treatment}\nDischarge Condition: Stable\nPatient has completed the current inpatient episode.\nOutpatient Advice: {followup}\nPhysician: {doctor}",
"DISCHARGE RECORD - MEDICAL SERVICES\nHospital: {hospital}\nPatient: {patient}\nRecord Number: {claim}\nDate Admitted: {admission}\nDate Released: {discharge}\nDiagnosis: {diagnosis}\nTreatment Summary: {treatment}\nCondition on Leaving Hospital: Stable\nDischarge Plan: {followup}\nSigned by Discharging Consultant: {doctor}",
"INPATIENT EPISODE CLOSURE NOTE\nPatient Name: {patient}\nHospital Reference: {claim}\nFacility: {hospital}\nStart of Stay: {admission}\nEnd of Stay: {discharge}\nClinical Diagnosis: {diagnosis}\nInterventions: {treatment}\nDisposition: Discharged from inpatient service.\nCondition: Stable\nFollow-up Care: {followup}\nConsultant: {doctor}",
"DISCHARGE SUMMARY FOR INSURANCE RECORD\nInsured Patient: {patient}\nClaim Number: {claim}\nHospital: {hospital}\nAdmission Date: {admission}\nDischarge Date: {discharge}\nFinal Diagnosis: {diagnosis}\nTreatment Provided: {treatment}\nOutcome of Hospitalization: Stable at discharge.\nPost-discharge Recommendation: {followup}\nAttending Doctor: {doctor}",
"WARD DISCHARGE HANDOVER\nPatient: {patient}\nMRN: {claim}\nWard Facility: {hospital}\nAdmission: {admission}\nDischarge: {discharge}\nDiagnosis at Release: {diagnosis}\nTreatment During Admission: {treatment}\nNursing / Clinical Status: Stable\nDischarge Advice: {followup}\nConsultant Approval: {doctor}\nPatient released from ward care.",
"DISCHARGE CLINICAL ABSTRACT\nName: {patient}\nHospital: {hospital}\nCase Reference: {claim}\nInpatient Dates: {admission} through {discharge}\nPrimary Diagnosis: {diagnosis}\nClinical Management: {treatment}\nResult: Patient stable and discharged.\nRecommended Review: {followup}\nTreating Specialist: {doctor}",
"FINAL SUMMARY OF TREATMENT\nPatient Details: {patient}\nProvider: {hospital}\nClaim Reference: {claim}\nAdmitted: {admission}\nDischarged: {discharge}\nFinal Clinical Impression: {diagnosis}\nTreatment and Monitoring: {treatment}\nCondition at Completion: Stable\nPlan After Discharge: {followup}\nDischarge Authorized By: {doctor}",
],
"hospital_bill": [
"HOSPITAL TAX INVOICE\nInvoice Number: {claim}\nInvoice Date: {discharge}\nBilled To: {patient}\nHospital: {hospital}\nITEMIZED CHARGES\nRoom and Nursing Charges: INR {room}\nDoctor Consultation: INR {doctor_fee}\nMedicines and Pharmacy: INR {medicine}\nProcedure Charges: INR {procedure}\nLaboratory Services: INR {lab}\nSubtotal: INR {subtotal}\nTax: INR {tax}\nTOTAL AMOUNT PAYABLE: INR {total}\nAmount Received: INR {paid}\nBalance Due: INR {balance}\nPayment Status: {payment}",
"DETAILED PATIENT BILL\nHealthcare Provider: {hospital}\nPatient Name: {patient}\nBilling Reference: {claim}\nService Period: {admission} to {discharge}\nAccommodation and Bed: INR {room}\nMedical Consultation: INR {doctor_fee}\nPharmacy Supplies: INR {medicine}\nDiagnostic Procedures: INR {lab}\nOther Procedures: INR {procedure}\nNet Charges: INR {subtotal}\nInvoice Total: INR {total}\nPaid: INR {paid}\nOutstanding: INR {balance}\nStatus: {payment}",
"FINAL INPATIENT ACCOUNT STATEMENT\nAccount Holder: {patient}\nFacility: {hospital}\nAccount Number: {claim}\nInvoice Date: {discharge}\nWard / Room: INR {room}\nProfessional Fees: INR {doctor_fee}\nDrugs and Consumables: INR {medicine}\nInvestigations: INR {lab}\nTreatment Procedures: INR {procedure}\nGross Amount: INR {subtotal}\nTax Amount: INR {tax}\nGrand Total: INR {total}\nPayment Received: INR {paid}\nAmount Outstanding: INR {balance}",
"PHARMACY AND HOSPITAL SERVICES INVOICE\nBill To: {patient}\nHospital Name: {hospital}\nBill Reference: {claim}\nRoom Charges: INR {room}\nConsultant Fees: INR {doctor_fee}\nPharmacy Charges: INR {medicine}\nLaboratory Charges: INR {lab}\nProcedure Charges: INR {procedure}\nTotal Before Tax: INR {subtotal}\nTax: INR {tax}\nInvoice Amount: INR {total}\nPayment Status: {payment}\nBalance Payable: INR {balance}",
"CONSOLIDATED MEDICAL BILL\nPatient: {patient}\nHospital: {hospital}\nInvoice ID: {claim}\nPatient Policy Reference: {policy}\nAccommodation: INR {room}\nClinical Services: INR {doctor_fee}\nMedicines: INR {medicine}\nDiagnostics: INR {lab}\nProcedures: INR {procedure}\nSubtotal: INR {subtotal}\nTax: INR {tax}\nAmount Charged: INR {total}\nAmount Paid: INR {paid}\nDue Amount: INR {balance}",
"INPATIENT BILLING SUMMARY\nName: {patient}\nMedical Facility: {hospital}\nBill Number: {claim}\nParticulars / Charges\nRoom and nursing: INR {room}\nDoctor and specialist: INR {doctor_fee}\nMedicines: INR {medicine}\nTests and investigations: INR {lab}\nProcedures: INR {procedure}\nTotal Charges: INR {total}\nReceived from patient: INR {paid}\nPending amount: INR {balance}\nPayment: {payment}",
"STATEMENT OF ACCOUNT - HOSPITAL\nCustomer / Patient: {patient}\nService Provider: {hospital}\nStatement Reference: {claim}\nBilling Period: {admission} - {discharge}\nBed occupancy: INR {room}\nMedical attendance: INR {doctor_fee}\nPharmacy: INR {medicine}\nDiagnostic services: INR {lab}\nProcedures: INR {procedure}\nTotal Debit: INR {total}\nCredits / Receipts: INR {paid}\nClosing Balance: INR {balance}",
"MEDICAL EXPENSE INVOICE\nInvoice Ref: {claim}\nPatient: {patient}\nHospital: {hospital}\nDate of Issue: {discharge}\nAccommodation: INR {room}\nConsultation: INR {doctor_fee}\nMedication: INR {medicine}\nLaboratory: INR {lab}\nProcedure: INR {procedure}\nTaxable Value: INR {subtotal}\nTax: INR {tax}\nTotal Invoice Value: INR {total}\nPaid Amount: INR {paid}\nBalance: INR {balance}",
"PATIENT BILLING LEDGER\nHospital: {hospital}\nPatient Account Name: {patient}\nLedger ID: {claim}\nTransaction Date: {discharge}\nDebit - Room / Bed: INR {room}\nDebit - Doctor Services: INR {doctor_fee}\nDebit - Pharmacy: INR {medicine}\nDebit - Diagnostics: INR {lab}\nDebit - Procedures: INR {procedure}\nTotal Debits: INR {total}\nPayments / Credits: INR {paid}\nNet Outstanding: INR {balance}",
"FINAL SETTLEMENT BILL\nPatient Name: {patient}\nHospital Name: {hospital}\nSettlement Number: {claim}\nRoom Rent: INR {room}\nNursing and Consultation: INR {doctor_fee}\nMedicines and Consumables: INR {medicine}\nDiagnostic Tests: INR {lab}\nProcedural Services: INR {procedure}\nSubtotal: INR {subtotal}\nTax: INR {tax}\nFinal Amount: INR {total}\nAmount Settled: INR {paid}\nRemaining Balance: INR {balance}",
"ITEMIZED INVOICE FOR MEDICAL SERVICES\nSupplier: {hospital}\nCustomer: {patient}\nInvoice No: {claim}\nAccommodation, INR {room}\nConsultation, INR {doctor_fee}\nPharmacy, INR {medicine}\nLaboratory, INR {lab}\nProcedures, INR {procedure}\nSubtotal INR {subtotal}\nTax INR {tax}\nTotal Due INR {total}\nPaid INR {paid}\nBalance INR {balance}",
"HOSPITAL RECEIPT AND BALANCE STATEMENT\nReceived From: {patient}\nHospital: {hospital}\nReceipt / Bill No: {claim}\nReceipt Date: {discharge}\nTotal Hospital Charges: INR {total}\nPayment Received: INR {paid}\nBalance Remaining: INR {balance}\nPayment Method: Insurance / Patient\nPayment Status: {payment}\nCharges include room, consultation, pharmacy, diagnostics and procedures.",
"INVOICE FOR INPATIENT SERVICES\nPatient / Debtor: {patient}\nProvider: {hospital}\nInvoice Reference: {claim}\nAdmission Period: {admission} - {discharge}\nRoom Services: INR {room}\nProfessional Services: INR {doctor_fee}\nDrug and Supply Charges: INR {medicine}\nLaboratory and Imaging: INR {lab}\nOther Procedures: INR {procedure}\nInvoice Total: INR {total}\nAmount Remitted: INR {paid}\nOutstanding Amount: INR {balance}",
"HOSPITAL CHARGES ABSTRACT\nFacility: {hospital}\nPatient: {patient}\nBilling ID: {claim}\nAccommodation INR {room}\nMedical consultation INR {doctor_fee}\nPharmacy INR {medicine}\nDiagnostics INR {lab}\nProcedures INR {procedure}\nTotal before tax INR {subtotal}\nTax INR {tax}\nTotal payable INR {total}\nAmount paid INR {paid}\nBalance due INR {balance}",
"CASH COUNTER FINAL BILL\nHospital: {hospital}\nPatient Name: {patient}\nCounter Bill: {claim}\nRoom / Ward: INR {room}\nConsultation: INR {doctor_fee}\nMedicines: INR {medicine}\nLab Tests: INR {lab}\nProcedures: INR {procedure}\nTax: INR {tax}\nNet Payable: INR {total}\nTendered: INR {paid}\nBalance: INR {balance}\nStatus: {payment}",
"PATIENT EXPENSE STATEMENT\nName of Patient: {patient}\nHospital: {hospital}\nReference: {claim}\nDate of Billing: {discharge}\nHospitalization Charges: INR {room}\nDoctor Fees: INR {doctor_fee}\nMedical Supplies: INR {medicine}\nDiagnostic Charges: INR {lab}\nProcedure Charges: INR {procedure}\nTotal Expenses: INR {total}\nPayment Received: INR {paid}\nBalance Payable: INR {balance}",
],
"signed_claim_form": [
"HEALTH INSURANCE CLAIM FORM\nSECTION A - INSURED DETAILS\nName of Insured: {patient}\nPolicy Number: {policy}\nClaim Reference: {claim}\nDate of Birth: {dob}\nContact Number: {phone}\nSECTION B - HOSPITAL DETAILS\nHospital: {hospital}\nSECTION C - CLAIM DETAILS\nClaim Category: {claim_type}\nAdmission Date: {admission}\nDischarge Date: {discharge}\nDeclaration: I confirm that the information provided is true and complete.\nI authorize the insurer to obtain records required to assess this claim.\nSignature of Insured: SIMULATED SIGNATURE\nDate Signed: {signed}",
"MEDICAL REIMBURSEMENT APPLICATION\nTo: {insurer}\nApplicant / Policyholder: {patient}\nPolicy ID: {policy}\nClaim Number: {claim}\nHospital Attended: {hospital}\nTreatment Period: {admission} to {discharge}\nBenefit Requested: {claim_type}\nBank Details: Submitted with supporting documents.\nDeclaration: I request reimbursement under my policy and certify that the details are accurate.\nApplicant Signature: SIMULATED SIGNATURE\nSubmission Date: {signed}",
"CASHLESS HOSPITALIZATION CLAIM REQUEST\nInsurer: {insurer}\nMember Name: {patient}\nPolicy Reference: {policy}\nPreauthorization / Claim ID: {claim}\nProvider Name: {hospital}\nRequested Claim Type: Cashless Hospitalization\nAdmission Date: {admission}\nI authorize the hospital and insurer to exchange information for claim processing.\nMember Declaration: Information supplied is complete to the best of my knowledge.\nSignature of Member: SIMULATED SIGNATURE\nDate: {signed}",
"SIGNED PATIENT CLAIM DECLARATION\nClaimant Details\nPatient Name: {patient}\nPolicy Number: {policy}\nClaim Reference: {claim}\nHospital Details: {hospital}\nDates of Treatment: {admission} - {discharge}\nClaim Purpose: {claim_type}\nDeclaration and Consent: I declare that the expenses submitted relate to the treatment stated above.\nI permit verification of medical and billing records by {insurer}.\nSignature of Claimant: SIMULATED SIGNATURE\nSigned On: {signed}",
"INSURANCE BENEFIT CLAIM FORM\nPolicyholder Information\nFull Name: {patient}\nPolicy No: {policy}\nMember Contact: {phone}\nHospitalization Information\nHospital Name: {hospital}\nClaim Number: {claim}\nAdmission: {admission}\nDischarge: {discharge}\nRequested Benefit: {claim_type}\nDeclaration: I certify that all statements and attached records are correct.\nInsured Signature: SIMULATED SIGNATURE\nDate: {signed}",
"CLAIMANT AUTHORIZATION AND CONSENT\nI, {patient}, holder of policy {policy}, submit claim {claim}.\nHospital / Provider: {hospital}\nTreatment Dates: {admission} to {discharge}\nClaim Type: {claim_type}\nI authorize {insurer} to contact the hospital and treating doctor for relevant records.\nI confirm that the information submitted is accurate and complete.\nSignature of Policyholder: SIMULATED SIGNATURE\nDate of Authorization: {signed}",
"HEALTH PLAN REIMBURSEMENT FORM\nMember / Insured Person: {patient}\nInsurance Company: {insurer}\nMember Policy ID: {policy}\nClaim Tracking Number: {claim}\nHospital or Nursing Home: {hospital}\nDates of Hospitalization: {admission} - {discharge}\nReimbursement Requested For: {claim_type}\nPatient Declaration: I have reviewed this application and the attached particulars.\nSignature of Applicant: SIMULATED SIGNATURE\nApplication Date: {signed}",
"COMPLETED MEDICAL EXPENSE CLAIM\nApplicant Name: {patient}\nPolicy Reference: {policy}\nClaim ID: {claim}\nHealthcare Institution: {hospital}\nTreatment Start: {admission}\nTreatment End: {discharge}\nNature of Claim: {claim_type}\nDeclaration: I certify that the expenses and particulars are genuine.\nConsent: I permit the insurer to verify the submitted information.\nApplicant Signature: SIMULATED SIGNATURE\nDate Submitted: {signed}",
"POLICYHOLDER CLAIM SUBMISSION\nInsured Member: {patient}\nInsurer: {insurer}\nPolicy Number: {policy}\nClaim Reference Number: {claim}\nProvider: {hospital}\nHospitalization Dates: {admission} through {discharge}\nClaim Benefit: {claim_type}\nStatement of Truth: I confirm that the answers in this form are complete.\nAuthorization to Process: I consent to claim assessment and record verification.\nSigned by Member: SIMULATED SIGNATURE\nDate: {signed}",
"PATIENT REIMBURSEMENT REQUEST\nClaimant: {patient}\nPolicy ID: {policy}\nReference No: {claim}\nHospital Name: {hospital}\nPeriod of Care: {admission} to {discharge}\nRequested Coverage: {claim_type}\nPayment Details: Bank information provided separately.\nDeclaration: I request payment of eligible medical expenses under the policy.\nI certify that no material information has been withheld.\nClaimant Signature: SIMULATED SIGNATURE\nDate: {signed}",
"INSURED PERSON DECLARATION FORM\nName: {patient}\nDate of Birth: {dob}\nPolicy Number: {policy}\nClaim Number: {claim}\nHospital: {hospital}\nAdmission Date: {admission}\nDischarge Date: {discharge}\nClaim Category: {claim_type}\nDeclaration: The particulars given are true and the attached documents relate to this claim.\nSignature: SIMULATED SIGNATURE\nDate Signed: {signed}",
"APPLICATION FOR MEDICAL CLAIM SETTLEMENT\nSubmitted To: {insurer}\nApplicant: {patient}\nPolicy / Certificate: {policy}\nClaim Reference: {claim}\nHospital: {hospital}\nTreatment Dates: {admission} - {discharge}\nSettlement Requested: {claim_type}\nUndertaking: I declare that the information and supporting records are accurate.\nI agree to provide further information if requested for claim assessment.\nSignature of Applicant: SIMULATED SIGNATURE\nSubmission Date: {signed}",
"GROUP HEALTH INSURANCE CLAIM FORM\nEmployee / Member Name: {patient}\nGroup Policy: {policy}\nClaim Tracking ID: {claim}\nInsurer: {insurer}\nHospital Facility: {hospital}\nHospitalization From: {admission}\nHospitalization To: {discharge}\nClaim Type: {claim_type}\nMember Declaration: I confirm the details are correct and authorize verification.\nMember Signature: SIMULATED SIGNATURE\nDate: {signed}",
"CLAIM FORM - DECLARATION BY INSURED\nInsured Name: {patient}\nPolicy Number: {policy}\nClaim Reference: {claim}\nHospital / Medical Provider: {hospital}\nTreatment Period: {admission} to {discharge}\nBenefit Applied For: {claim_type}\nI hereby declare that the information in this application is true.\nI authorize the insurer to obtain relevant medical records for processing.\nSignature of Insured Person: SIMULATED SIGNATURE\nDate of Declaration: {signed}",
"MEDICAL INSURANCE CLAIM APPLICATION\nApplicant Particulars\nName: {patient}\nPolicy: {policy}\nClaim No: {claim}\nHospital Particulars\nFacility: {hospital}\nDates: {admission} - {discharge}\nRequested Benefit: {claim_type}\nDeclaration and Authorization: I confirm the accuracy of this claim and consent to verification.\nSigned by: {patient}\nSignature: SIMULATED SIGNATURE\nDate: {signed}",
"FINAL CLAIMANT CONSENT FORM\nI, {patient}, insured under policy {policy}, submit reference {claim}.\nMedical Provider: {hospital}\nHospital Stay: {admission} through {discharge}\nRequested Claim Benefit: {claim_type}\nI declare that the documents submitted are genuine and complete.\nI authorize {insurer} to contact the hospital for claim-related information.\nClaimant Signature: SIMULATED SIGNATURE\nSigned Date: {signed}",
],
}


def add_ocr_noise(text):
    # Same noise policy for all classes; most samples retain readable structure.
    if rng.random() < 0.30:
        text = " ".join(text.split())
    else:
        text = "\n".join(line.strip() for line in text.splitlines() if line.strip())
    if rng.random() < 0.15:
        text = text.replace(": ", " ", 1)
    if rng.random() < 0.10:
        text = re.sub(r" {2,}", " ", text)
    if rng.random() < 0.15:
        swaps = {"0": "O", "1": "I", "O": "0", "I": "1"}
        chars = list(text)
        choices = [i for i, ch in enumerate(chars) if ch in swaps]
        if choices:
            i = rng.choice(choices)
            chars[i] = swaps[chars[i]]
            text = "".join(chars)
    if rng.random() < 0.06:
        words = text.split()
        choices = [i for i, word in enumerate(words) if word.isalpha() and len(word) >= 9]
        if choices:
            i = rng.choice(choices)
            word = words[i]
            cut = rng.randint(3, len(word)-3)
            words[i] = word[:cut] + " " + word[cut:]
            text = " ".join(words)
    return text


def generate_rows():
    rows = []
    for label in LABELS:
        if len(T[label]) != 16:
            raise ValueError(f"{label} has {len(T[label])} templates; expected 16")
        for split, config in SPLITS.items():
            indices = list(config["templates"])
            for _ in range(config["count"]):
                template = T[label][rng.choice(indices)]
                text = add_ocr_noise(template.format(**make_values()))
                rows.append({"text": text, "label": label, "split": split})
    rng.shuffle(rows)
    return rows


def validate(rows):
    if len(rows) != 1600:
        raise ValueError(f"Expected 1600 rows, got {len(rows)}")
    texts = [row["text"] for row in rows]
    if any(not text.strip() for text in texts):
        raise ValueError("Empty text found")
    if len(texts) != len(set(texts)):
        raise ValueError("Duplicate document text found")
    split_template_sets = {name: set(cfg["templates"]) for name, cfg in SPLITS.items()}
    names = list(split_template_sets)
    for i, first in enumerate(names):
        for second in names[i+1:]:
            if split_template_sets[first] & split_template_sets[second]:
                raise ValueError(f"Template leakage between {first} and {second}")
    for split, config in SPLITS.items():
        for label in LABELS:
            count = sum(r["split"] == split and r["label"] == label for r in rows)
            if count != config["count"]:
                raise ValueError(f"Unexpected count for {split}/{label}: {count}")


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    if OUTPUT_FILE.exists():
        raise FileExistsError(f"{OUTPUT_FILE} already exists. Rename it before generating.")
    rows = generate_rows()
    validate(rows)
    with OUTPUT_FILE.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["text", "label", "split"])
        writer.writeheader()
        writer.writerows(rows)
    print("\nDataset V3 generated successfully")
    print("Output:", OUTPUT_FILE)
    print("Total examples:", len(rows))
    for split, config in SPLITS.items():
        print(f"\n{split.upper()}: {config['count'] * len(LABELS)} total; {config['count']} per class")
        print("Template family indices:", list(config["templates"]))
        for label in LABELS:
            print(f"  {label}: {sum(r['split'] == split and r['label'] == label for r in rows)}")
    print("\nAll split template families are disjoint.")
    print("CSV columns: text, label, split")


if __name__ == "__main__":
    main()
