function validateUsername(input) {
    const length = input.value.length;
    const helper = document.getElementById('usernameHelper');
    
    if (length < 5 || length > 12) {
        helper.textContent = '用户名长度必须在5-12位之间';
        helper.style.color = 'red';
        return false;
    }
    helper.textContent = '用户名格式正确';
    helper.style.color = 'green';
    return true;
}

function checkPasswordStrength(input) {
    const password = input.value;
    const strengthIndicator = document.getElementById('strengthIndicator');
    const strengthText = document.getElementById('strengthText');
    const submitBtn = document.getElementById('submitBtn');
    
    // 计算密码强度
    let strength = 0;
    if (password.length >= 8) strength++;
    if (/[A-Z]/.test(password)) strength++;
    if (/[a-z]/.test(password)) strength++;
    if (/[0-9]/.test(password)) strength++;
    if (/[^A-Za-z0-9]/.test(password)) strength++;
    
    // 更新强度显示
    const strengthLevels = ['', '弱', '中', '强'];
    const strengthColors = ['', '#ff4444', '#ffbb33', '#00C851'];
    
    strengthIndicator.style.width = `${(strength / 4) * 100}%`;
    strengthIndicator.style.backgroundColor = strengthColors[strength] || strengthColors[0];
    strengthText.textContent = strengthLevels[strength] || '';
    
    // 只有密码强度达到"中"或以上才能提交
    submitBtn.disabled = strength < 2;
    return strength >= 2;
}

// 添加确认密码验证
function validateConfirmPassword(input) {
    const password = document.querySelector('input[name="password"]').value;
    const confirmPassword = input.value;
    const helper = document.getElementById('confirmPasswordHelper');
    
    if (password !== confirmPassword) {
        helper.textContent = '两次输入的密码不一致';
        helper.style.color = 'red';
        return false;
    }
    helper.textContent = '密码一致';
    helper.style.color = 'green';
    return true;
}

// 添加表单提交处理
document.getElementById('registerForm')?.addEventListener('submit', function(e) {
    e.preventDefault();
    
    if (!validateUsername(this.username) || 
        !checkPasswordStrength(this.password) || 
        !validateConfirmPassword(this.confirmPassword)) {
        return;
    }

    const formData = new FormData(this);

    fetch('/api/register', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            window.location.href = '/login';
        } else {
            document.getElementById('errorMsg').innerText = data.message || '注册失败，请重试';
        }
    })
    .catch(error => {
        document.getElementById('errorMsg').innerText = '注册失败，请重试';
    });
});
