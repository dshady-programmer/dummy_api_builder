"""
Defining model to hold fields for each
tables

This allows the user to define something like this

Name = db.Column(db.String)
Age = db.Column(db.Integer)
_Id = db.Column(db.Integer, primary_key=True)
"""
from . import db
import enum



parameter_constraints = db.Table('parameter_constraint',
                                 db.Column('tableparameter_id', db.Integer, db.ForeignKey('tableparameter.id', name='fk_parameter_constraint_tableparameter_id', ondelete='CASCADE')),
                                 db.Column('constraint_id', db.Integer, db.ForeignKey('constraint.id', name='fk_parameter_constraint_constraint_id', ondelete='CASCADE')),
                                 db.UniqueConstraint('tableparameter_id', 'constraint_id', name='uq_tableparameter_constraint')
                                 )

   

class DataTypes(enum.Enum):
    """
        Data type enum map for the supported data types of a table parameter
    """
    string = 'String'
    decimal = 'Decimal'
    text = 'Text'
    integer = 'Integer'
    boolean = 'Boolean'
    date = 'date'
    datetime = 'datetime'

class TableLevelOnDeleteOptions(enum.Enum):

    """
        Table level foreign key On-Delete options 
    """

    cascade = 'CASCADE'
    protect = 'PROTECT'


class RowLevelOndeleteOptions(enum.Enum):
    """
        Row level foreign key On-Delete options
    """
    cascade = 'CASCADE'
    protect = 'PROTECT'
    set_null = 'SET_NULL'



class TableParameter(db.Model):

    """
        TableParameter model to keep track of the fields for each table (table columns)
        id: autoincrement, model primary key
        name: Name of the field
        data_type: Data type of the field (can either be string, decimal, text, integer, boolean, date, datetime)
        primary_key: True if this table parameter is a primary key of the table (There can be more than one, in the case of composite keys)
        foreign_key_reference_id: If the column is foreign key, this field would be a reference to the foreign key reference table of the foreign key itself
                                  e.g 
                                  Car - table
                                     - name
                                     - make
                                     - year
                                     - country (foreign key to Country table)
                                       foreign_key_reference_id would be 'Country'.reference (this maps to the foreignkeyreferencetable for Country)

        dataType_length: The maximum length expected for a data entry. This is only valid for strings, text and integers
        default_value: A user default value for this column if none is given
                       - Behaves differently based on the table constraints..
                          - for foreign key, the default value must be inputed by the user and would be validated against a valid entry with that value on the foreign key table
                          - for primary key would be generated automatically and ignore any default value passed by the user. The generation would be based on the data type of the primary key
                              ** if the data type is integer, generates a random value every new entry added to the table
                              ** if the data type is string, generates a unique uuid value for every new entry added to the table
                              note: This would only generate those values if users don't pass in a value on entry creation
                          - a unique column can't have a default value
        table_id: Foreign key to the Table model
        table: Relationship to the Table model for back reference (tableparameter.table gives the table the parameter belongs to)
        constraints: Many to many Relationship to the Constraint model for back reference (tableparameter.constraints gives all constraints on the parameter)
        entries: Relationship to the Entry model for back reference (tableparameter.entries gives all entries for the parameter)
                 note: tableparameter.entries would give all entries for the parameter across all entry_lists in a table.
                       It's similar to grabbing only a car name from a car table with 1000 rows. It would give all 1000 car names in the table.

    """
    __tablename__ = 'tableparameter'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String, nullable=False)
    data_type = db.Column(db.Enum(DataTypes), default=DataTypes.string, nullable=False)
    primary_key = db.Column(db.Boolean, default=False) 
    foreign_key_reference_id = db.Column(db.Integer, db.ForeignKey('foreignkeyfieldreferencetable.id', ondelete='CASCADE'), nullable=True, index=True) 
    dataType_length = db.Column(db.Integer, nullable=True) # Only valid for strings, text, integers
    default_value = db.Column(db.Text, nullable=True) # for default values

    foreign_key_default_value_id = db.Column(db.Integer, db.ForeignKey('entrylist.id', ondelete='SET NULL'), nullable=True) # if field has a foreign key constraint and default value
    foreign_key_default_value = db.relationship('Entrylist', back_populates="table_param_defaults")

    table_id = db.Column(db.Integer, db.ForeignKey('table.id', ondelete='CASCADE'), index=True)
    table = db.relationship('Table', back_populates='table_parameters')
    constraints = db.relationship('Constraint', secondary=parameter_constraints, backref='table_parameters')
    entries = db.relationship('Entry', back_populates='tableparameter', cascade="all, delete-orphan", passive_deletes=True)

    table_level_on_delete = db.Column(db.Enum(TableLevelOnDeleteOptions), default=TableLevelOnDeleteOptions.protect, nullable=False) # on delete behavior for the table level foreign key relationship. It can be either CASCADE, PROTECT.
    row_level_on_delete = db.Column(db.Enum(RowLevelOndeleteOptions), default=RowLevelOndeleteOptions.protect, nullable=False) # on delete behavior for the row level foreign key relationship. It can be either CASCADE, PROTECT or SET_NULL.

    __table_args__ = (
        db.UniqueConstraint('table_id', 'name', name='uq_tableparameter_table_id_name'),
        {'sqlite_autoincrement': True}  # Ensure that the id is always incremented and not reused after deletion
    )