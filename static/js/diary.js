const DiaryAPI = {
    add: async function(data) {
        try {
            const response = await fetch('/add', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(data)
            });
            
            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.error || '发布失败');
            }
            
            return await response.json();
        } catch (error) {
            console.error('Error:', error);
            throw error;
        }
    },
    async delete(id) {
        try {
            const response = await fetch(`/api/diary/${id}`, {
                method: 'DELETE',
                headers: {'Content-Type': 'application/json'},
                credentials: 'same-origin'
            });
            
            const result = await response.json();
            if (!response.ok) throw new Error(result.error || '操作失败');
            return result;
            
        } catch (error) {
            console.error('Delete diary error:', error);
            throw error;
        }
    },
    
    async update(id, data) {
        try {
            const response = await fetch(`/edit/${id}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                },
                credentials: 'same-origin',
                body: JSON.stringify(data)
            });
            
            const result = await response.json();
            if (!response.ok) throw new Error(result.error || '操作失败');
            return result;
            
        } catch (error) {
            console.error('Update diary error:', error);
            throw error;
        }
    }
};

// 错误处理
function handleError(error, defaultMessage = '操作失败，请重试') {
    mdui.snackbar({
        message: error.message || defaultMessage,
        timeout: 2000
    });
}

function submitDiary(url, formData) {
    return fetch(url, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            content: formData.get('content'),
            is_public: formData.get('is_public') === 'true',
            mood: formData.get('mood'),
            location: formData.get('location'),
            date: formData.get('date')
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            window.location.href = '/mydiary';
        } else {
            alert(data.error || '保存失败');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('提交失败，请重试');
    });
}

// 添加日记的处理函数
document.addEventListener('DOMContentLoaded', function() {
    const addForm = document.querySelector('#diary-form');
    if (addForm) {
        addForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const formData = new FormData(this);
            submitDiary('/add', formData);
        });
    }
    
    // 编辑日记的处理函数
    const editForm = document.querySelector('#edit-diary-form');
    if (editForm) {
        editForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const diaryId = this.getAttribute('data-diary-id');
            const formData = new FormData(this);
            submitDiary(`/edit/${diaryId}`, formData);
        });
    }
});
