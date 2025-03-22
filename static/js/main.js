// MDUI 组件初始化
document.addEventListener('DOMContentLoaded', function() {
    // 初始化侧边栏
    var drawer = new mdui.Drawer('#main-drawer');
    
    // 密码验证
    const passwordInput = document.getElementById('password');
    const confirmPasswordInput = document.getElementById('confirmPassword');
    if (confirmPasswordInput) {
        confirmPasswordInput.addEventListener('input', function() {
            if (passwordInput.value !== confirmPasswordInput.value) {
                confirmPasswordInput.setCustomValidity('两次输入的密码不一致');
            } else {
                confirmPasswordInput.setCustomValidity('');
            }
        });
    }
    
    // 表单验证
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            if (!form.checkValidity()) {
                e.preventDefault();
                e.stopPropagation();
            }
            form.classList.add('was-validated');
        });
    });
});

// 通用的表单提交处理
async function submitForm(url, formData, method = 'POST') {
    try {
        const response = await fetch(url, {
            method: method,
            headers: {
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest'
            },
            credentials: 'same-origin',
            body: JSON.stringify(Object.fromEntries(formData))
        });
        
        const result = await response.json();
        if (result.success) {
            mdui.snackbar({
                message: '操作成功',
                timeout: 1500,
                onClose: () => {
                    if (result.redirect) {
                        window.location.href = result.redirect;
                    }
                }
            });
        } else {
            throw new Error(result.error || '操作失败');
        }
    } catch (error) {
        mdui.snackbar({
            message: error.message || '操作失败，请重试',
            timeout: 2000
        });
    }
}
