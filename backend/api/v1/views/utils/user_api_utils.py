
from models import TableParameter
def update_api_fk_rel_tables_on_update(old_name, new_name):
    #update tableparameter foreign_key_reference_field

    TblPs = TableParameter.query.filter(TableParameter.foreign_key_reference_field.startswith(old_name)).all()
    for tb in TblPs:
        prev_fk_ref_field = tb.foreign_key_reference_field
        tb.foreign_key_reference_field = prev_fk_ref_field.replace(old_name, new_name)
    
    
    #update Relationship fk_rel and fk_model_name.

def delete_api_fk_rel_tables_on_delete(name):
    #delete tableparameter foreign_key_reference_field
    TableParameter.query.filter(TableParameter.foreign_key_reference_field.startswith(name)).delete(synchronize_session=False)


    #update Relationship fk_rel and fk_model_name.