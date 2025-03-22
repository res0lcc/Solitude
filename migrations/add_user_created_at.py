from alembic import op
import sqlalchemy as sa
from datetime import datetime

def upgrade():
    # 添加 created_at 列，允许为空以便添加列
    op.add_column('user', sa.Column('created_at', sa.DateTime, nullable=True))
    
    # 为现有记录设置默认时间
    op.execute("UPDATE user SET created_at = NOW() WHERE created_at IS NULL")
    
    # 修改列为不允许为空
    op.alter_column('user', 'created_at',
        existing_type=sa.DateTime(),
        nullable=False
    )

def downgrade():
    op.drop_column('user', 'created_at')
