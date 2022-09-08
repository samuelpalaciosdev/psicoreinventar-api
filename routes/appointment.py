from re import S
from flask import Flask, jsonify, request, url_for, Blueprint
from flask_jwt_extended import get_jwt_identity, jwt_required
from werkzeug.security import generate_password_hash, check_password_hash
from models import User, Appointment, Invoice

appointment = Blueprint('appointment', __name__)

@appointment.route('/appointment', methods=['POST'])
@jwt_required()
def add_appointment():
    # Appointment
    id = get_jwt_identity()
    user = User.query.get(id)
    pacient_id = user.id
    dateTime = request.json.get('dateTime')
    doctor_id = request.json.get('doctor_id')
    service_id = request.json.get('service_id')
    status = "Pendiente"

    # check if there is already an appointment booked by the current patient, in the same dateTime with the same doctor
    check_for_booked_appointment_by_patient = Appointment.query.filter_by(dateTime=dateTime, doctor_id=doctor_id, pacient_id=pacient_id).first()  
    if check_for_booked_appointment_by_patient: return jsonify({'status': 'failed', 'message': 'Ya agendaste esta cita'}), 400 

    # check if there is already an appointment booked in the same dateTime with the same doctor
    check_for_booked_appointment = Appointment.query.filter_by(dateTime=dateTime, doctor_id=doctor_id).first()  
    if check_for_booked_appointment: return jsonify({'status': 'failed', 'message': 'Cita ya agendada (no disponible)'}), 400 

    # check if there is already an appointment booked by the current patient, in the same dateTime with different doctor
    check_for_booked_appointment_by_date = Appointment.query.filter_by(dateTime=dateTime, pacient_id=pacient_id).first()
    if check_for_booked_appointment_by_date: return jsonify({'status': 'failed', 'message': 'Ya tienes una cita agendada, a esta misma fecha y hora'}), 400 
    
    # if user selects initial appointment (service_id = 1)
    # check if the patient has booked an initial appointment before (free appointment = 1 time)
    if service_id == 1:
        check_for_initial_appointment_booked = Appointment.query.filter_by(doctor_id=doctor_id, service_id=1, pacient_id=pacient_id).first()
        if check_for_initial_appointment_booked: return jsonify({'status': 'failed', 'message': 'Solo puedes agendar una consulta inicial por especialista'}), 400 


    appointment = Appointment()

    appointment.dateTime = dateTime
    appointment.pacient_id = pacient_id
    appointment.doctor_id = doctor_id
    appointment.service_id = service_id
    appointment.status = status
    # Setting default status as Pendiente ===  appointment.status = "Pendiente"


    invoice = Invoice()
    # should be linked to stripe but currently is just the datetime of the appointment
    invoice.date_of_purchase = dateTime # should be date_of_purchase but what is mentioned above
    invoice.pacient_id = user.id
    invoice.service_id = service_id

    #relationship of appointment with invoice
    appointment.invoice = invoice
    appointment.save()

    data = {
        'appointment': appointment.serialize()
    }

    # if add appointment succeded
    if appointment: return jsonify({'status': 'success', 'message': 'Cita agendada exitosamente', 'data': data}), 200
    else: return jsonify({'status': 'failed', 'message': 'Cita no agendada, intente nuevamente', 'data': None}), 200

@appointment.route('/appointment_from_doctor', methods=['POST'])
@jwt_required()
def add_appointment_from_doctor_dashboard():
    # Appointment
    id = get_jwt_identity()
    user = User.query.get(id)
    doctor_id = user.id
    dateTime = request.json.get('dateTime')
    pacient_id = request.json.get('pacient_id')
    service_id = request.json.get('service_id')
    status = "Pendiente"

    # check if there is already an appointment booked by the current doctor, in the same dateTime with the same patient
    check_for_booked_appointment_by_patient = Appointment.query.filter_by(dateTime=dateTime, doctor_id=doctor_id, pacient_id=pacient_id).first()  
    if check_for_booked_appointment_by_patient: return jsonify({'status': 'failed', 'message': 'Ya agendaste esta cita'}), 400 

    # check if there is already an appointment booked in the same dateTime with the same patient
    check_for_booked_appointment = Appointment.query.filter_by(dateTime=dateTime, pacient_id=pacient_id).first()  
    if check_for_booked_appointment: return jsonify({'status': 'failed', 'message': 'Cita ya agendada (no disponible)'}), 400 

    # check if there is already an appointment booked by the current doctor, in the same dateTime with different patient
    check_for_booked_appointment_by_date = Appointment.query.filter_by(dateTime=dateTime, doctor_id=doctor_id).first()
    if check_for_booked_appointment_by_date: return jsonify({'status': 'failed', 'message': 'Ya tienes una cita agendada, a esta misma fecha y hora'}), 400 
    
    # if user selects initial appointment (service_id = 1)
    # check if the patient has booked an initial appointment before (free appointment = 1 time)
    if service_id == 1:
        check_for_initial_appointment_booked = Appointment.query.filter_by(doctor_id=doctor_id, service_id=1, pacient_id=pacient_id).first()
        if check_for_initial_appointment_booked: return jsonify({'status': 'failed', 'message': 'Solo puedes agendar una consulta inicial por especialista'}), 400 


    appointment = Appointment()

    appointment.dateTime = dateTime
    appointment.doctor_id = doctor_id
    appointment.pacient_id = pacient_id
    appointment.service_id = service_id
    appointment.status = status
    # Setting default status as Pendiente ===  appointment.status = "Pendiente"


    invoice = Invoice()
    # should be linked to stripe but currently is just the datetime of the appointment
    invoice.date_of_purchase = dateTime # should be date_of_purchase but what is mentioned above
    invoice.pacient_id = pacient_id
    invoice.service_id = service_id

    #relationship of appointment with invoice
    appointment.invoice = invoice
    appointment.save()

    data = {
        'appointment': appointment.serialize()
    }

    # if add appointment succeded
    if appointment: return jsonify({'status': 'success', 'message': 'Cita agendada exitosamente', 'data': data}), 200
    else: return jsonify({'status': 'failed', 'message': 'Cita no agendada, intente nuevamente', 'data': None}), 200
# Get appointment by date
@appointment.route('/appointment_by_date', methods=['POST'])
def get_appointment_by_date():
    dateTime = request.json.get('dateTime')

    appointments = Appointment.query.filter_by(dateTime=dateTime)
    appointments = list(map(lambda appointment: appointment.serialize(), appointments))
    
    return jsonify(appointments), 200

# Get appointments with certain service_id
@appointment.route('/appointment_by_service_id', methods=['POST'])
def get_appointment_by_service_id():
    service_id = request.json.get('service_id')

    appointments = Appointment.query.filter_by(service_id=service_id)
    appointments = list(map(lambda appointment: appointment.serialize(), appointments))
    
    return jsonify(appointments), 200

# Get all appointments with service_id 1
@appointment.route('/initial_appointments', methods=['POST'])
def get_initial_appointments():
    appointments = Appointment.query.filter_by(service_id=1)
    appointments = list(map(lambda appointment: appointment.serialize(), appointments))
    
    return jsonify(appointments), 200

# Edit (Reagendar fecha y hora) appoinment
@appointment.route('/edit_appoinment/<int:id>', methods=['PUT'])
@jwt_required()
def edit_appoinment(id):
    appointment = Appointment.query.filter_by(id=id).first()
    dateTime = request.json.get('dateTime')
    doctor_id = request.json.get('doctor_id')

    # Check if appointment doesn't exist
    if not appointment:  return jsonify({ "status": "failed", "code": 404, "message": "Cita no encontrada", "data": None }), 404

    # Check if doctor already has a booked appointment in that dateTime

    check_for_booked_appointment = Appointment.query.filter_by(dateTime=dateTime, doctor_id=doctor_id).first()  
    if check_for_booked_appointment: return jsonify({'status': 'failed', 'message': 'Cita ya agendada'}), 400 

    # Update dateTime of appointment
    appointment.dateTime = dateTime

    appointment.update()

    data = {
        'appointment': appointment.serialize()
    }
    return jsonify({'status': 'success', 'message': 'Cita reagendada', 'data': data}), 200

# Edit appointment status (Pendiente/Realizada)

@appointment.route('/edit_appoinment_status/<int:id>', methods=['PUT'])
@jwt_required()
def edit_appointment_status(id):
    appointment = Appointment.query.filter_by(id=id).first()
    status = request.json.get('status')

    # Check if appointment doesn't exist
    if not appointment:  return jsonify({ "status": "failed", "code": 404, "message": "Cita no encontrada", "data": None }), 404

    # Update status of appointment
    appointment.status = status

    appointment.update()

    data = {
        'appointment': appointment.serialize()
    }
    return jsonify({'status': 'success', 'message': 'Estado de cita actualizado', 'data': data}), 200

@appointment.route('/delete_appoinment/<int:id>', methods=['DELETE'])
@jwt_required()
def delete_appoinment(id):
    appointment = Appointment.query.filter_by(id=id).first()
    appointment.delete()
    return jsonify({'status': 'success', 'message': 'Appointment Deleted', 'data': None}), 200

# Get all appointments registrated
@appointment.route("/all_appointments", methods=["GET"])
def get_appointments():
    appointments = Appointment.query.all()
    appointments = list(map(lambda appointment: appointment.serialize(), appointments))
    return jsonify(appointments), 200

# Get appointment by id
@appointment.route('/appointments/<int:id>', methods=["GET"])
def get_appointment(id):
    appointment = Appointment.query.get(id)
    appointment = appointment.serialize()
    return jsonify(appointment), 200

# Get current user (client) appointments
@appointment.route("/client_appointments", methods=["GET"])
@jwt_required()
def get_client_appointments():
    id = get_jwt_identity()
    user = User.query.get(id)
    pacient_id = user.id
    appointments = Appointment.query.filter_by(pacient_id=pacient_id)
    appointments = list(map(lambda appointment: appointment.serialize(), appointments))
    return jsonify(appointments), 200

# Get all clients appointment history
@appointment.route('/appointment_history')
def get_appointment_history():
    appointments = Appointment.query.filter_by(status="Realizada").all()
    appointments = list(map(lambda appointment: appointment.serialize(), appointments))
    return jsonify(appointments), 200

# Get certain client appointment history
@appointment.route('/appointment_history/<int:id>')
def get_appointment_history_by_user_id(id):
    user = User.query.get(id)
    pacient_id = user.id
    appointments = Appointment.query.filter_by(pacient_id=pacient_id,status="Realizada").all()
    appointments = list(map(lambda appointment: appointment.serialize(), appointments))
    return jsonify(appointments), 200

# Get curren user (client) history of appointments based on done (Realizada) status

@appointment.route('/client_appointment_history', methods=['GET'])
@jwt_required()
def get_client_appointments_history():
    id = get_jwt_identity()
    user = User.query.get(id)
    pacient_id = user.id
    appointments = Appointment.query.filter_by(pacient_id=pacient_id, status="Realizada")
    appointments = list(map(lambda appointment: appointment.serialize(), appointments))
    return jsonify(appointments), 200

# Get current user (doctor) appointments
@appointment.route("/doctor_appointments", methods=["GET"])
@jwt_required()
def get_doctor_appointments():
    id = get_jwt_identity()
    user = User.query.get(id)
    doctor_id = user.id
    appointments = Appointment.query.filter_by(doctor_id=doctor_id)
    appointments = list(map(lambda appointment: appointment.serialize(), appointments))
    return jsonify(appointments), 200