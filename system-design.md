\# System Design Write-up



\## 1. Overview



The Healthcare Appointment \& Follow-up Manager is designed to provide reliable appointment scheduling while preventing conflicting bookings and handling doctor availability changes safely. The backend is built using Flask, SQLAlchemy, and PostgreSQL, with dedicated models and route modules for appointments, doctor availability, leave, consultations, notifications, reminders, and slot holds.



The system follows a transactional approach for operations that can create scheduling conflicts. PostgreSQL acts as the source of truth for appointment state and availability.



\## 2. Double-Booking Prevention



Double-booking is prevented through multiple layers of validation.



When a patient attempts to book an appointment, the backend first validates that the requested doctor exists, the requested time is valid, and the doctor is available during that period. It then checks for existing appointments that overlap with the requested time slot.



The important part is that availability checking and appointment creation are performed within a database transaction. This reduces the possibility of two simultaneous requests both observing the same slot as available.



A slot hold mechanism is also used for temporary reservation during the booking process. Once a slot is held, another patient cannot successfully claim the same slot while the hold is active.



The final appointment creation is committed only after all required validations succeed. If any validation fails, the transaction is rolled back and the patient receives an appropriate error response.



This combination of application-level validation, temporary slot locking, and transactional database operations provides protection against accidental and concurrent double-booking.



\## 3. Doctor Leave Conflict Handling



Doctor leave is treated as an availability constraint. A doctor should not have appointments scheduled during approved leave periods.



When leave is created or modified, the system checks whether existing appointments conflict with the requested leave period. A conflicting appointment is identified when its scheduled time overlaps the doctor's leave interval.



The system does not silently create leave while ignoring existing appointments. Instead, the conflict is detected and the operation can be rejected or handled according to the application's defined business rules.



During normal appointment booking, the availability logic also considers doctor leave. Therefore, even if a time slot falls within the doctor's configured working hours, it is not considered bookable when the doctor is on leave.



This ensures that working hours and leave are evaluated together rather than treating working hours as the only source of availability.



\## 4. Slot Hold Mechanism



The slot hold mechanism temporarily reserves an appointment slot before the appointment is permanently created.



This is useful when booking involves multiple steps, such as selecting a slot, validating patient information, processing additional information, and finally confirming the appointment.



A slot hold contains information identifying the doctor, the requested time slot, the user making the hold, and its expiration state. The hold is temporary and should not be treated as a confirmed appointment.



When a user attempts to reserve a slot, the backend checks whether an active hold or confirmed appointment already exists for that time. If the slot is free, a hold is created.



The hold has a limited lifetime. Once it expires, the slot becomes available again. This prevents abandoned booking sessions from permanently blocking appointment times.



Before final confirmation, the system verifies that the hold is still valid. If it has expired or another conflict has occurred, appointment creation is rejected. Otherwise, the appointment can be created and the temporary hold can be released or marked as consumed.



This mechanism improves concurrency handling and reduces race conditions during appointment booking.



\## 5. Notification Failure Handling



Notifications are treated as a separate operation from the core appointment transaction. Appointment creation should not be incorrectly rolled back merely because an email or reminder service temporarily fails.



After an appointment or relevant healthcare event is successfully stored, the system can generate a notification or reminder task. Notification processing is therefore decoupled from the critical database operation.



If notification delivery fails, the failure should be recorded through application logging and/or notification status information. The appointment itself remains stored because the healthcare scheduling operation has already succeeded.



The notification and reminder components can retry failed operations where appropriate. Temporary failures such as network errors or external email-service downtime should therefore not cause loss of appointment data.



The system also maintains notification-related records so that delivery status can be tracked independently from the appointment.



This separation provides better reliability: the database remains the authoritative source for appointments, while external notification services are treated as dependent services that may temporarily become unavailable.



\## 6. Reliability Summary



The overall design uses database transactions, availability validation, temporary slot holds, conflict detection, and independent notification processing to make appointment scheduling reliable.



The key principles are:



\* Validate doctor availability before booking.

\* Prevent overlapping appointments.

\* Consider doctor leave when calculating availability.

\* Temporarily hold slots during the booking process.

\* Expire unused holds automatically.

\* Keep appointment persistence independent from notification delivery.

\* Record and handle notification failures without losing confirmed appointment data.



Together, these mechanisms provide a safer scheduling workflow and reduce common problems such as double-booking, booking during doctor leave, abandoned reservations, and notification-service failures.



