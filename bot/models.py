from sqlalchemy import String, Integer, Date, Time, ForeignKey, Enum, DateTime, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, Mapped, mapped_column
import enum

Base = declarative_base()


class DaysOfWeek(enum.Enum):
    mon = 'Понедельник'
    tue = 'Вторник'
    wed = 'Среда'
    thu = 'Четверг'
    fri = 'Пятница'
    sat = 'Суббота'
    sun = 'Воскресенье'


class Trainer(Base):
    __tablename__ = 'training_trainer'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    first_name: Mapped[str] = mapped_column(String(20), nullable=False)
    last_name: Mapped[str] = mapped_column(String(20), nullable=False)
    phone_number: Mapped[str] = mapped_column(String(12), unique=True, nullable=False)
    trainertg_id: Mapped[str | None] = mapped_column(String(16), unique=True, nullable=True)

    trainings: Mapped[list["Training"]] = relationship('Training', back_populates='trainer')

    def __repr__(self):
        return f"<Trainer(name='{self.first_name} {self.last_name}', phone='{self.phone_number}')>"


class Training(Base):
    __tablename__ = 'training_training'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(64), nullable=False)
    trainer_id: Mapped[int | None] = mapped_column(ForeignKey('training_trainer.id'), nullable=True)
    trainer: Mapped["Trainer"] = relationship('Trainer', back_populates='trainings')
    start_date: Mapped[Date] = mapped_column(Date, nullable=False)
    end_date: Mapped[Date] = mapped_column(Date, nullable=False)

    schedules: Mapped[list["TrainingSchedule"]] = relationship('TrainingSchedule', back_populates='training')
    attendances: Mapped[list["Attendance"]] = relationship('Attendance', back_populates='training')
    prices: Mapped[list["Price"]] = relationship('Price', back_populates='training')

    def __repr__(self):
        return self.name

    def clean(self):
        if self.end_date < self.start_date:
            raise ValueError("Дата окончания не может быть раньше даты начала.")


class TrainingSchedule(Base):
    __tablename__ = 'training_trainingschedule'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    training_id: Mapped[int] = mapped_column(ForeignKey('training_training.id'), nullable=False)
    training: Mapped["Training"] = relationship('Training', back_populates='schedules')
    day_of_week: Mapped[DaysOfWeek] = mapped_column(Enum(DaysOfWeek), nullable=False)
    start_time: Mapped[Time] = mapped_column(Time, nullable=False)
    end_time: Mapped[Time] = mapped_column(Time, nullable=False)

    def __repr__(self):
        return f"{self.day_of_week} {self.start_time}-{self.end_time}"


class Attendance(Base):
    __tablename__ = 'training_attendance'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    training_id: Mapped[int] = mapped_column(ForeignKey('training_training.id'), nullable=False)
    training: Mapped["Training"] = relationship('Training', back_populates='attendances')
    attend_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    recording_day: Mapped[DaysOfWeek] = mapped_column(Enum(DaysOfWeek), nullable=False)
    recording_date: Mapped[Date] = mapped_column(Date, nullable=False)
    created_date: Mapped[DateTime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    update_date: Mapped[DateTime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now(),
                                                  nullable=False)

    def __repr__(self):
        return f'На занятие {self.training.name} пришло {self.attend_count} чел. Дата {self.recording_date}'


class Price(Base):
    __tablename__ = 'training_price'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    training_id: Mapped[int] = mapped_column(ForeignKey('training_training.id'), nullable=False)
    training: Mapped["Training"] = relationship('Training', back_populates='prices')
    quantity_to: Mapped[int] = mapped_column(Integer, nullable=False)
    price_to: Mapped[int] = mapped_column(Integer, nullable=False)
    quantity_from: Mapped[int] = mapped_column(Integer, nullable=False)
    price_from: Mapped[int] = mapped_column(Integer, nullable=False)

    def __repr__(self):
        return f'Цена до {self.quantity_to} чел. включительно: {self.price_to}, цена от {self.quantity_from} чел. включительно: {self.price_from}'


Trainer.trainings = relationship('Training', order_by=Training.id, back_populates='trainer')
Training.schedules = relationship('TrainingSchedule', order_by=TrainingSchedule.id, back_populates='training')
Training.attendances = relationship('Attendance', order_by=Attendance.id, back_populates='training')
Training.prices = relationship('Price', order_by=Price.id, back_populates='training')
Attendance.training = relationship('Training', back_populates='attendances')
Price.training = relationship('Training', back_populates='prices')
TrainingSchedule.training = relationship('Training', back_populates='schedules')

