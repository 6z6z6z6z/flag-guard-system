"""add location to trainings

Revision ID: add_location_to_trainings
Revises: 
Create Date: 2024-03-13 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_location_to_trainings'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # 添加 location 字段
    op.add_column('trainings', sa.Column('location', sa.String(200), nullable=False, server_default=''))
    
    # 更新现有记录
    op.execute("UPDATE trainings SET location = '' WHERE location IS NULL")

def downgrade():
    # 删除 location 字段
    op.drop_column('trainings', 'location') 