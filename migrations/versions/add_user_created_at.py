from alembic import op
import sqlalchemy as sa
from datetime import datetime

def upgrade():
    # 使用更安全的方式添加列
    op.add_column('user', 
        sa.Column('created_at', 
            sa.DateTime, 
            nullable=True, 
            server_default=sa.text('CURRENT_TIMESTAMP')
        )
    )
    
    # 更新现有记录的时间戳
    op.execute("UPDATE user SET created_at = CURRENT_TIMESTAMP")
    
    # 将列设置为非空
    op.alter_column('user', 'created_at',
        existing_type=sa.DateTime(),
        nullable=False,
        server_default=sa.text('CURRENT_TIMESTAMP')
    )

def downgrade():
    op.drop_column('user', 'created_at')
