
from models import db, TableParameter, Relationship
def update_api_fk_rel_tables_on_update(old_name, new_name):
    #update tableparameter foreign_key_reference_field

    TblPs = TableParameter.query.filter(TableParameter.foreign_key_reference_field.startswith(old_name)).all()
    for tb in TblPs:
        prev_fk_ref_field = tb.foreign_key_reference_field
        tb.foreign_key_reference_field = prev_fk_ref_field.replace(old_name, new_name)
    
    
    #update Relationship fk_rel and fk_model_name.
    rels = Relationship.query.filter(Relationship.fk_rel.startswith(old_name)).all()
    for rel in rels:
        prev_rel_key = rel.fk_rel
        rel.fk_rel = prev_rel_key.replace(old_name, new_name)

def delete_api_fk_rel_tables_on_delete(name):
    # delete tableparameter foreign_key_reference_field
    TableParameter.query.filter(TableParameter.foreign_key_reference_field.startswith(name)).delete(synchronize_session=False)


    # delete Relationship fk_rel and fk_model_name.
    # in v2 an on_delete feature would be added for now default is cascade
    rels = Relationship.query.filter(Relationship.fk_rel.startswith(old_name)).all()


    for rel in rels:
        rel.entrylists.clear()
        db.session.delete(rel)