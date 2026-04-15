# Katkı Rehberi

Bu depo ders projesi kurallarına (`AGENTS.md`) ve katmanlı Django mimarisine uyar.

## Dal (branch) adlandırma

| Önek | Kullanım |
|-------|----------|
| `feature/<kisa-aciklama>` | Yeni özellik |
| `fix/<kisa-aciklama>` | Hata düzeltmesi |
| `chore/<kisa-aciklama>` | Araç, bağımlılık, dokümantasyon (davranış değişmez) |
| `security/<kisa-aciklama>` | Güvenlik düzeltmesi |

`main` doğrudan push yerine PR kullanın (organizasyon politikası ile uyumlu).

## Commit mesajları

[Conventional Commits](https://www.conventionalcommits.org/) tarzı önerilir:

- `feat: öğrenci transcript filtreleme`
- `fix: enrollment POST çift tıklama kenarı`
- `docs: README kurulum güncellemesi`
- `chore: ruff satır sonu ayarı`
- `security: bağımlılık CVE düzeltmesi`

Gövde: **ne** ve **neden** (isteğe bağlı); tek satırda anlaşılır özet zorunlu.

## Pull request

1. Şablonu doldurun: `.github/pull_request_template.md`.
2. **CI yeşil**: lint, güvenlik taraması, test + coverage eşiği (`pyproject.toml` `fail_under`, Makefile `ci` hedefi farklı olabilir — PR açıklamasında belirtin).
3. **Migration**: şema değişikliğinde `makemigrations` + etki/geri alma notu.
4. **İş kuralları**: enrollment, GPA, transcript akışlarına dokunuyorsanız ilgili testleri çalıştırın (`core/test_phase4.py`, `core/test_phase6.py`, pytest işaretli testler).

## Kod standartları

- İş mantığını mümkün olduğunca **servis katmanına** (`core/services/`, uygulama `services.py`) taşıyın; view ince kalsın.
- Korumalı view’larda **kimlik doğrulama + rol** kontrolü.
- ORM dışı SQL yok (zorunluysa parametreli ve gerekçeli).
- Türkçe kullanıcı arayüzü metinleri şablonlarda; çeviri için `locale/` akışına `AGENTS.md` bakın.

## Yerel doğrulama (özet)

```bash
pip install -r requirements-dev.txt
python -m ruff check .
python manage.py test
# veya tam kapı (Linux/WSL, bash):
make ci
```

Windows’ta `make` yoksa yukarıdaki `ruff` + `manage.py test` + `SECURITY_OVERVIEW.md` içindeki güvenlik komutlarını kullanın.
