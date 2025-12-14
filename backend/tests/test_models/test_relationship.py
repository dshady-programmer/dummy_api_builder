"""
Testing relationship model, testing foreign key relationship

This feature is fully tested in the test_views package
"""

from tests import TestConfig
from models.table import Table
from models.api import Api
from models.user import User
from models.tableparameter import TableParameter
from models.constraints import Constraint
from models.entry import Entry
from models.entrylist import EntryList
from models.relationship import Relationship
import sqlalchemy

# class TableParameterContext()
class TestTableParameter(TestConfig):
    """
      Full test on the Relationship model
    """
    def setUp(self):
        super().setUp()

    def cls_setup(self):
        """
        create a setup context for testing entry methods since they'd depend on the user, api and table
        """
        self.user1 = User(email='user1@test.com', password='password')
        self.api1 = Api(name="Blog", description="blog api")

        self.db.session.add_all([self.user1, self.api1])
        self.db.session.commit()
        # Adding the api to a specific user
        self.api1.user_id = self.user1.id
        self.table1 = Table(name="User", description="User table", api_id=self.api1.id)
        self.table2 = Table(name="Post", description="Post table", api_id=self.api1.id)
        self.db.session.add(self.table1)
        self.db.session.add(self.table2)
        self.db.session.commit()
        self.Tb_id = TableParameter(name="_id", table_id=self.table1.id, data_type="integer", primary_key=True)
        self.Tb_name = TableParameter(name="name", table_id=self.table1.id) # Creates a table parameter of name, by default it'll would have a data type of string    
        self.Tb_age = TableParameter(name="age", data_type="integer", table_id=self.table1.id)
        self.Tb_created = TableParameter(name="created", data_type="date", table_id=self.table1.id)
        self.Tb_isStaff = TableParameter(name="isStaff", data_type="boolean", table_id=self.table1.id)
        self.Tb_email = TableParameter(name="email", dataType_length=20, table_id=self.table1.id)
        self.Tb2_id = TableParameter(name="_id", table_id=self.table2.id, data_type="integer", primary_key=True)
        self.Tb2_title = TableParameter(name="title", table_id=self.table2.id, dataType_length=100, data_type="string")
        self.Tb2_content = TableParameter(name="content", table_id=self.table2.id, data_type="text")
        self.Tb2_author = TableParameter(name="author", table_id=self.table2.id, foreign_key_reference_id=self.table1.reference.id) # foreign key, with the reference field referenceing the User table in the Blog api
        self.db.session.add_all([
            self.Tb_id,self.Tb_age, self.Tb_email, self.Tb_name, self.Tb_created, self.Tb_isStaff,
            self.Tb2_id, self.Tb2_title, self.Tb2_content, self.Tb2_author
              ])
        self.db.session.commit()
        self.tabl_entrylist_user1 = EntryList(table_id=self.table1.id)
        self.tabl_entrylist_post1 = EntryList(table_id=self.table2.id)
        self.pk = Constraint(name="primary_key")
        self.fk = Constraint(name="foreign_key")
        self.nullable = Constraint(name="nullable")
        self.unique = Constraint(name="unique")
        self.db.session.add_all([self.pk, self.fk, self.unique, self.nullable, self.tabl_entrylist_user1, self.tabl_entrylist_post1])
        self.db.session.commit()
        # Add table parameters using reverse relationship
        self.pk.table_parameters.append(self.Tb_id)
        self.fk.table_parameters.append(self.Tb2_author) # added the foreign constraint to author table parameter.
        self.unique.table_parameters.extend([self.Tb_id, self.Tb_email, self.Tb2_id])
        self.nullable.table_parameters.append(self.Tb_age)
        

    def test_entry_creation_with_foreign_key(self):
        """
        Test creating an entry based on above tableparameters created above
        """
        with self.app.app_context():
            self.cls_setup()

            tb_id_entry1 = Entry(value="1", tableparameter_id=self.Tb_id.id, entry_list_id=self.tabl_entrylist_user1.id)
            tb_name_entry1 = Entry(value="Peter", tableparameter_id = self.Tb_name.id, entry_list_id=self.tabl_entrylist_user1.id)
            tb_age_entry1 = Entry(value="20", tableparameter_id=self.Tb_age.id, entry_list_id=self.tabl_entrylist_user1.id)
            tb_email_entry1 = Entry(value="test@test.com", tableparameter_id=self.Tb_email.id, entry_list_id=self.tabl_entrylist_user1.id)
            tb_created_entry1 = Entry(value="2024-02-07", tableparameter_id=self.Tb_created.id, entry_list_id=self.tabl_entrylist_user1.id)
            tb_isstaff_entry1 = Entry(value="True", tableparameter_id=self.Tb_isStaff.id, entry_list_id=self.tabl_entrylist_user1.id)
        
            tb2_id_entry = Entry(value="1", tableparameter_id=self.Tb2_id.id, entry_list_id=self.tabl_entrylist_post1.id)
            tb2_title_entry = Entry(value="First title", tableparameter_id=self.Tb2_title.id, entry_list_id=self.tabl_entrylist_post1.id)
            tb2_content_entry = Entry(value="Content to the first title", tableparameter_id=self.Tb2_content.id, entry_list_id=self.tabl_entrylist_post1.id)
            tb2_author_entry = Entry(value="1", tableparameter_id=self.Tb2_author.id, entry_list_id=self.tabl_entrylist_post1.id)

            self.db.session.add_all([
                tb_id_entry1, tb_name_entry1, tb_age_entry1, tb_email_entry1, tb_created_entry1, tb_isstaff_entry1,
                tb2_id_entry, tb2_title_entry, tb2_content_entry, tb2_author_entry
            ])
            self.db.session.commit()

            self.tabl_entrylist_user1.primary_key_value = tb_id_entry1.id
            self.tabl_entrylist_post1.primary_key_value = tb2_id_entry.id
            
            # creating a relationship between the 2 entrylist

            # entry_ref_pk would be  "1" as it is a reference to the user primary key which we want to create a foreign key to
            # fk_rel (foreign key relationship chain) following the format 'parentapi.table->childapi.table.field' would be Blog.User->Blog.Post.author
            # fk_model_name is the query name for the foreign key data on the parent table. e.g user1.blog_posts 

            # Note: this feature is fully tested in the test_views package
            rel = Relationship(entry_ref_pk="1", foreign_key_rel_id=self.table1.reference.id, child_table_id=self.tabl_entrylist_post1.table_id)
            rel.entrylists.append(self.tabl_entrylist_user1) # relationship has been created
            self.db.session.add(rel)
            self.db.session.commit()

            self.assertEqual(len(rel.entrylists), 1)
            expected_parent = self.tabl_entrylist_user1

            p_id = rel.entry_ref_pk
            p_table = rel.foreign_key_rel.table_reference

            parent_entrylist = EntryList.query.filter_by(primary_key_value=p_id, table_id=p_table.id).first()

            self.assertEqual(parent_entrylist, expected_parent)


