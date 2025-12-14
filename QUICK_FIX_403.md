# ⚡ Быстрое решение ошибки 403

## Проблема
```
Permission to ab0vee/Phoenix_lab_ML.git denied to INSOLENTik.
403 Forbidden
```

## 🎯 Быстрое решение

### Если репозиторий `ab0vee/Phoenix_lab_ML` - ВАШ:

#### Шаг 1: Создайте Personal Access Token
1. Откройте: https://github.com/settings/tokens
2. "Generate new token (classic)"
3. Название: `Phoenix Lab`
4. Срок: `90 days` или `No expiration`
5. Отметьте `repo` (полный доступ)
6. "Generate token"
7. **СКОПИРУЙТЕ ТОКЕН** (показывается 1 раз!)

#### Шаг 2: Удалите старые учетные данные
```powershell
git credential-manager erase https://github.com
```

#### Шаг 3: Запушьте снова
```powershell
git push -u origin main
```
**При запросе:**
- Username: `ab0vee` (ваш GitHub username)
- Password: **вставьте токен** (не обычный пароль!)

---

### Если репозиторий НЕ ваш (нужен свой):

#### Шаг 1: Создайте свой репозиторий
1. Откройте: https://github.com/new
2. Название: `Phoenix-LAB` (или любое)
3. **НЕ добавляйте** README, .gitignore
4. "Create repository"

#### Шаг 2: Измените remote
```powershell
git remote remove origin
git remote add origin https://github.com/INSOLENTik/название-вашего-репозитория.git
git push -u origin main
```

**При запросе:**
- Username: `INSOLENTik` (ваш GitHub username)
- Password: токен (создайте на https://github.com/settings/tokens)

---

## ✅ Готово!

После успешного пуша проверьте на GitHub - все файлы должны быть там.

