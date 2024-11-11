import { Title, Container, Main } from '../../components'
import styles from './styles.module.css'
import MetaTags from 'react-meta-tags'

const Technologies = () => {
  return (
    <Main>
      <MetaTags>
        <title>О проекте</title>
        <meta name="description" content="Фудграм - Технологии" />
        <meta property="og:title" content="О проекте" />
      </MetaTags>

      <Container>
        <h1 className={styles.title}>Технологии</h1>
        <div className={styles.content}>
          <div>
            <h2 className={styles.subtitle}>Технологии, которые применены в этом проекте:</h2>
            <div className={styles.text}>
              <ul className={styles.textItem}>
                <li className={styles.textItem}>
                  <a href="https://www.python.org/" className={styles.textLink}>
                    Python
                  </a>
                </li>
                <li className={styles.textItem}>
                  <a href="https://www.djangoproject.com/" className={styles.textLink}>
                    Django
                  </a>
                </li>
                <li className={styles.textItem}>
                  <a href="https://www.django-rest-framework.org/" className={styles.textLink}>
                    Django REST Framework
                  </a>
                </li>
                <li className={styles.textItem}>
                  <a href="https://djoser.readthedocs.io/" className={styles.textLink}>
                    Djoser
                  </a>
                </li>
              </ul>
            </div>
          </div>
        </div>
      </Container>
    </Main>
  )
}

export default Technologies
