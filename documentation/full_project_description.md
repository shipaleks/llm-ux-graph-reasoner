# План системы графового анализа и синтеза знаний

## 0. Предварительный опрос и определение контекста исследования

### Цель:
Определить контекст исследования, ожидания пользователя и специфику предметной области для фокусирования последующего анализа.

### Алгоритм:
1. **Сбор информации о задаче и ожиданиях**
   - **Промпт для интерфейса (RU):**
     ```
     Пожалуйста, опишите:
     
     1. Какие тексты вы анализируете (научные статьи, художественная литература, интервью, документация)?
     2. Что вы хотите узнать в результате анализа?
     3. Есть ли у вас первоначальные гипотезы или предположения?
     4. Какие аспекты текста вас особенно интересуют?
     5. Какой тип вывода вы ожидаете получить (научная теория, интерпретация, практические рекомендации)?
     ```

   - **Промпт для интерфейса (EN):**
     ```
     Please describe:
     
     1. What kind of texts are you analyzing (scientific articles, fiction, interviews, documentation)?
     2. What do you want to learn from this analysis?
     3. Do you have any initial hypotheses or assumptions?
     4. Which aspects of the text are you particularly interested in?
     5. What type of output do you expect to receive (scientific theory, interpretation, practical recommendations)?
     ```

2. **Определение доменно-специфичных параметров**
   - **Промпт для LLM (RU):**
     ```
     На основе следующей информации от пользователя:
     
     {ответы пользователя на вопросы}
     
     Определите:
     
     1. Тип текста и предметную область (например, научные статьи по биологии, UX-интервью, литературное произведение)
     2. Ключевые термины и концепции, которые следует отслеживать
     3. Типы отношений, наиболее релевантные для данной области
     4. Предпочтительный уровень абстракции для конечных выводов
     5. Специфичные для домена метрики качества анализа
     
     Представьте результат в JSON-формате с полями: domain_type, key_concepts, relation_types, abstraction_level, quality_metrics.
     ```

   - **Промпт для LLM (EN):**
     ```
     Based on the following information from the user:
     
     {user's answers to questions}
     
     Determine:
     
     1. Text type and domain area (e.g., scientific articles in biology, UX interviews, literary work)
     2. Key terms and concepts to track
     3. Relationship types most relevant to this domain
     4. Preferred level of abstraction for final conclusions
     5. Domain-specific quality metrics for analysis
     
     Present the result in JSON format with fields: domain_type, key_concepts, relation_types, abstraction_level, quality_metrics.
     ```

3. **Настройка параметров системы**
   - На основе полученного JSON-ответа автоматическая установка параметров для всех последующих этапов
   - Специализация словарей и промптов под конкретную предметную область
   - Установка порогов и весов для различных типов отношений

### Инструменты:
- Интерфейс для структурированного опроса пользователя
- LLM для интерпретации ответов и определения параметров
- База предопределенных шаблонов для разных доменов (UX-исследования, литературный анализ, научные исследования)

### Обработка ошибок:
- Если LLM не может корректно определить параметры, система предложит выбрать из предопределенных шаблонов
- При противоречивых ответах пользователя система задаст уточняющие вопросы

### Выход:
JSON-структура с параметрами системы, адаптированными под конкретную задачу и предметную область.

## I. Контекстуальная сегментация и анализ текста

### Цель:
Разбить входной текст на осмысленные сегменты с сохранением контекстуальных связей и суммаризаций.

### Алгоритм:
1. **Загрузка и начальная обработка текста**
   - Чтение TXT-файлов с сохранением структуры
   - Нормализация форматирования (пробелы, переносы строк)
   - Определение естественных разделителей (заголовки, разделы, абзацы)

2. **Иерархическая сегментация**
   - **Промпт для LLM (RU):**
     ```
     Разделите следующий текст на иерархически организованные сегменты.
     
     Текст: {часть текста, до 10000 символов}
     
     Создайте структуру с следующими уровнями:
     1. Основные разделы (если есть)
     2. Подразделы (если есть)
     3. Логические блоки в пределах подразделов
     4. Отдельные абзацы или группы связанных предложений
     
     Для каждого сегмента укажите:
     - Уникальный ID (например, "1.2.3" для 3-го блока 2-го подраздела 1-го раздела)
     - Исходный текст
     - Позицию в документе (начало-конец в символах)
     
     Представьте результат в JSON-формате с вложенной структурой, отражающей иерархию.
     ```

   - **Промпт для LLM (EN):**
     ```
     Divide the following text into hierarchically organized segments.
     
     Text: {portion of text, up to 10000 characters}
     
     Create a structure with the following levels:
     1. Main sections (if any)
     2. Subsections (if any)
     3. Logical blocks within subsections
     4. Individual paragraphs or groups of related sentences
     
     For each segment, specify:
     - Unique ID (e.g., "1.2.3" for the 3rd block of the 2nd subsection of the 1st section)
     - Original text
     - Position in document (start-end in characters)
     
     Present the result in JSON format with a nested structure reflecting the hierarchy.
     ```

3. **Контекстуальная суммаризация**
   - **Промпт для LLM (RU):**
     ```
     Для каждого сегмента ниже создайте контекстуальную суммаризацию.
     
     Сегмент: {текст сегмента}
     ID: {ID сегмента}
     Родительский контекст: {вышестоящие сегменты в иерархии}
     
     Для каждого сегмента создайте:
     
     1. Краткая суммаризация (1-2 предложения)
     2. Ключевые тезисы (3-5 пунктов)
     3. Роль в структуре документа (например, "введение", "аргумент", "пример", "вывод")
     4. Связь с родительским контекстом (как этот сегмент развивает или иллюстрирует вышестоящие идеи)
     
     Представьте результат в JSON-формате с полями: id, summary, key_points, role, parent_relation.
     ```

   - **Промпт для LLM (EN):**
     ```
     For each segment below, create a contextual summarization.
     
     Segment: {segment text}
     ID: {segment ID}
     Parent context: {higher-level segments in hierarchy}
     
     For each segment, create:
     
     1. Brief summary (1-2 sentences)
     2. Key points (3-5 bullets)
     3. Role in document structure (e.g., "introduction", "argument", "example", "conclusion")
     4. Relation to parent context (how this segment develops or illustrates higher-level ideas)
     
     Present the result in JSON format with fields: id, summary, key_points, role, parent_relation.
     ```

4. **Кросс-сегментный анализ связей**
   - **Промпт для LLM (RU):**
     ```
     Проанализируйте связи между следующими сегментами текста:
     
     Сегмент 1: {текст сегмента 1 с ID}
     Сегмент 2: {текст сегмента 2 с ID}
     
     Определите:
     
     1. Наличие смысловой связи (да/нет)
     2. Тип связи:
        - Причина-следствие
        - Аргумент-контраргумент
        - Общая тема
        - Пример-иллюстрация
        - Развитие мысли
        - Противопоставление
        - Другое (укажите)
     3. Сила связи (0-1, где 1 - очень сильная)
     4. Направление (односторонняя/двусторонняя)
     5. Ключевые слова или фразы, указывающие на связь
     
     Представьте результат в JSON-формате.
     ```

   - **Промпт для LLM (EN):**
     ```
     Analyze the connections between the following text segments:
     
     Segment 1: {text of segment 1 with ID}
     Segment 2: {text of segment 2 with ID}
     
     Determine:
     
     1. Presence of meaningful connection (yes/no)
     2. Connection type:
        - Cause-effect
        - Argument-counterargument
        - Common theme
        - Example-illustration
        - Thought development
        - Contrast
        - Other (specify)
     3. Connection strength (0-1, where 1 is very strong)
     4. Direction (one-way/bidirectional)
     5. Key words or phrases indicating the connection
     
     Present the result in JSON format.
     ```

### Инструменты:
- Библиотеки для работы с текстом (например, Python + NLTK)
- Хранилище для иерархических данных (например, MongoDB)
- LLM API (Claude 3.7 Sonnet)

### Обработка ошибок:
- **Проблема: LLM неверно определяет структуру или выдает некорректный JSON**
  - Решение: Повторная отправка запроса с более структурированными инструкциями
  - Резервный метод: Использование правил на основе форматирования текста для базовой сегментации

- **Проблема: Сегментация слишком детальная или слишком общая**
  - Решение: Адаптивная настройка параметров сегментации на основе первых результатов

- **Проблема: Большие объемы текста вызывают превышение контекстного окна LLM**
  - Решение: Рекурсивная сегментация с промежуточной агрегацией результатов

### Выход:
Иерархически структурированный корпус текстовых сегментов с контекстуальными суммаризациями и выявленными связями.

## II. Извлечение сущностей и создание базового графа

### Цель:
Создать начальный граф знаний, извлекая сущности и отношения из сегментированного текста с учетом предметной области.

### Алгоритм:
1. **Доменно-ориентированное извлечение сущностей**
   - **Промпт для LLM (RU):**
     ```
     Извлеките значимые сущности из следующего текста, учитывая предметную область "{domain_type}".
     
     Текст: {текст сегмента с ID}
     
     Фокусируйтесь на следующих типах сущностей, релевантных для данной области:
     {key_concepts из предварительного опроса}
     
     Для каждой сущности укажите:
     
     1. Название (каноническая форма)
     2. Тип сущности (из списка выше или предложите свой, если необходимо)
     3. Контекст появления (цитата из текста)
     4. Атрибуты (свойства, характеристики, упомянутые в тексте)
     5. Роль в данном сегменте (основная тема, вспомогательный пример, определение и т.д.)
     6. Уверенность в значимости (0-1)
     
     Не извлекайте общие концепции или малозначимые сущности, фокусируйтесь на ключевых понятиях для данной области.
     Учитывайте, что одна и та же сущность может быть упомянута под разными именами или в разных формах.
     
     Представьте результат в JSON-формате с полями: name, type, context, attributes, role, confidence.
     ```

   - **Промпт для LLM (EN):**
     ```
     Extract significant entities from the following text, considering the domain of "{domain_type}".
     
     Text: {segment text with ID}
     
     Focus on the following entity types relevant to this domain:
     {key_concepts from preliminary survey}
     
     For each entity, specify:
     
     1. Name (canonical form)
     2. Entity type (from the list above or suggest your own if necessary)
     3. Context of appearance (quote from text)
     4. Attributes (properties, characteristics mentioned in the text)
     5. Role in this segment (main topic, supporting example, definition, etc.)
     6. Confidence in significance (0-1)
     
     Do not extract general concepts or minor entities; focus on key concepts for this domain.
     Keep in mind that the same entity may be mentioned under different names or in different forms.
     
     Present the result in JSON format with fields: name, type, context, attributes, role, confidence.
     ```

2. **Извлечение отношений с учетом домена**
   - **Промпт для LLM (RU):**
     ```
     Определите отношения между следующими сущностями в данном тексте, учитывая предметную область "{domain_type}".
     
     Текст: {текст сегмента}
     
     Сущности:
     {список извлеченных сущностей с ID и типами}
     
     Фокусируйтесь на следующих типах отношений, релевантных для данной области:
     {relation_types из предварительного опроса}
     
     Для каждой пары сущностей определите:
     
     1. Есть ли прямое отношение (да/нет)
     2. Тип отношения (из списка выше или предложите свой, если необходимо)
     3. Направление (от какой сущности к какой)
     4. Контекст отношения (цитата из текста)
     5. Сила отношения (0-1)
     6. Уверенность в наличии отношения (0-1)
     
     Не указывайте тривиальные или слишком общие отношения.
     Учитывайте как явные, так и неявные отношения, но различайте их по уровню уверенности.
     
     Представьте результат в JSON-формате с полями: source_entity, target_entity, relation_type, direction, context, strength, confidence.
     ```

   - **Промпт для LLM (EN):**
     ```
     Determine the relationships between the following entities in this text, considering the domain of "{domain_type}".
     
     Text: {segment text}
     
     Entities:
     {list of extracted entities with IDs and types}
     
     Focus on the following relationship types relevant to this domain:
     {relation_types from preliminary survey}
     
     For each pair of entities, determine:
     
     1. Whether there is a direct relationship (yes/no)
     2. Type of relationship (from the list above or suggest your own if necessary)
     3. Direction (from which entity to which)
     4. Context of the relationship (quote from text)
     5. Strength of the relationship (0-1)
     6. Confidence in the relationship's existence (0-1)
     
     Do not indicate trivial or overly general relationships.
     Consider both explicit and implicit relationships, but distinguish them by level of confidence.
     
     Present the result in JSON format with fields: source_entity, target_entity, relation_type, direction, context, strength, confidence.
     ```

3. **Разрешение кореференций и объединение сущностей**
   - **Промпт для LLM (RU):**
     ```
     Проанализируйте следующий список сущностей, извлеченных из разных сегментов текста, и определите, какие из них относятся к одному и тому же концепту.
     
     Сущности:
     {список сущностей с атрибутами и контекстами}
     
     Для каждой группы потенциально совпадающих сущностей:
     
     1. Определите, действительно ли это одна и та же сущность (да/нет)
     2. Если да, укажите каноническое имя для этой сущности
     3. Объясните причину решения (лексическое сходство, контекстуальное сходство, семантическое сходство)
     4. Уровень уверенности в решении (0-1)
     5. Объединенный список атрибутов из всех упоминаний
     
     Учитывайте:
     - Синонимы и вариации написания
     - Гиперонимы и гипонимы (родо-видовые отношения)
     - Метонимию (обозначение объекта через связанное понятие)
     - Анафорические ссылки (он, она, они, этот и т.д.)
     
     Представьте результат в JSON-формате с полями: entity_ids, canonical_name, merge_decision, reason, confidence, combined_attributes.
     ```

   - **Промпт для LLM (EN):**
     ```
     Analyze the following list of entities extracted from different text segments and determine which ones refer to the same concept.
     
     Entities:
     {list of entities with attributes and contexts}
     
     For each group of potentially matching entities:
     
     1. Determine if they are indeed the same entity (yes/no)
     2. If yes, specify the canonical name for this entity
     3. Explain the reason for the decision (lexical similarity, contextual similarity, semantic similarity)
     4. Level of confidence in the decision (0-1)
     5. Combined list of attributes from all mentions
     
     Consider:
     - Synonyms and spelling variations
     - Hypernyms and hyponyms (genus-species relationships)
     - Metonymy (designation of an object through a related concept)
     - Anaphoric references (he, she, they, this, etc.)
     
     Present the result in JSON format with fields: entity_ids, canonical_name, merge_decision, reason, confidence, combined_attributes.
     ```

4. **Формирование и верификация базового графа**
   - **Промпт для LLM (RU):**
     ```
     Проверьте следующий граф знаний на внутреннюю согласованность и логические противоречия.
     
     Узлы графа:
     {список объединенных сущностей с атрибутами}
     
     Рёбра графа:
     {список отношений между сущностями}
     
     Для каждого потенциального противоречия или несогласованности:
     
     1. Опишите несогласованность (например, циклическая зависимость, противоречивые атрибуты)
     2. Укажите вовлеченные узлы и рёбра
     3. Предложите решение (например, удаление одного из рёбер, уточнение атрибута)
     4. Оцените серьезность проблемы (критическая/средняя/низкая)
     
     Также проверьте:
     - Избыточные узлы и рёбра
     - Отсутствующие важные связи, которые следуют из имеющихся
     - Нарушения ограничений предметной области
     
     Представьте результат в JSON-формате с полями: issue_type, involved_elements, proposed_solution, severity.
     ```

   - **Промпт для LLM (EN):**
     ```
     Check the following knowledge graph for internal consistency and logical contradictions.
     
     Graph nodes:
     {list of merged entities with attributes}
     
     Graph edges:
     {list of relationships between entities}
     
     For each potential contradiction or inconsistency:
     
     1. Describe the inconsistency (e.g., cyclic dependency, contradictory attributes)
     2. Indicate the involved nodes and edges
     3. Suggest a solution (e.g., removing one of the edges, clarifying an attribute)
     4. Assess the severity of the problem (critical/medium/low)
     
     Also check for:
     - Redundant nodes and edges
     - Missing important connections that follow from existing ones
     - Violations of domain constraints
     
     Present the result in JSON format with fields: issue_type, involved_elements, proposed_solution, severity.
     ```

### Инструменты:
- LLM API (Claude 3.7 Sonnet)
- Библиотеки для работы с графами (NetworkX, PyGraphviz)
- Хранилище графов (Neo4j)

### Обработка ошибок:
- **Проблема: LLM не выдает структурированный JSON или выдает некорректный формат**
  - Решение: Поэтапная верификация JSON с повторными запросами для исправления
  - Резервный метод: Регулярные выражения и правила для извлечения базовой информации

- **Проблема: Противоречивые решения при разрешении кореференций**
  - Решение: Голосование нескольких промптов с различными формулировками
  - Резервный метод: Сохранение обоих вариантов с разными весами

- **Проблема: Слишком большое количество сущностей вызывает превышение контекста**
  - Решение: Пакетная обработка с последующим объединением результатов
  - Резервный метод: Фильтрация по предварительной оценке значимости

### Выход:
Верифицированный начальный граф знаний с объединенными сущностями и их отношениями, специфичными для предметной области.

## III. Структурный анализ графа и определение стратегии исследования

### Цель:
Проанализировать структуру созданного графа, выявить ключевые паттерны и определить направления дальнейшего исследования.

### Алгоритм:
1. **Расчет и анализ метрик центральности**
   - Вычисление основных метрик для каждого узла:
     - Степенная центральность (количество связей)
     - Центральность по близости (средняя длина пути до других узлов)
     - Центральность по посредничеству (частота появления на кратчайших путях)
     - Центральность по собственному вектору (связность с другими важными узлами)

   - **Промпт для LLM (RU):**
     ```
     Проанализируйте следующие метрики центральности для узлов графа знаний в контексте предметной области "{domain_type}".
     
     Данные по центральности узлов:
     {таблица с узлами и их метриками центральности}
     
     На основе этих данных определите:
     
     1. Топ-10 ключевых концепций, имеющих наибольшее влияние в данной области (с обоснованием выбора метрики)
     2. Структурные роли узлов:
        - "Хабы" (узлы с множеством связей)
        - "Мосты" (узлы, соединяющие различные области)
        - "Авторитеты" (узлы, на которые часто ссылаются)
        - "Периферийные" (важные узлы с малым количеством связей)
     3. Предположения о причинах высокой центральности определенных узлов
     4. Возможные пробелы в графе, где центральность неожиданно низкая
     
     Представьте результат в структурированном формате с разделами для каждой категории анализа.
     ```

   - **Промпт для LLM (EN):**
     ```
     Analyze the following centrality metrics for knowledge graph nodes in the context of the domain "{domain_type}".
     
     Node centrality data:
     {table with nodes and their centrality metrics}
     
     Based on this data, determine:
     
     1. Top 10 key concepts with the greatest influence in this domain (with justification for the chosen metric)
     2. Structural roles of nodes:
        - "Hubs" (nodes with multiple connections)
        - "Bridges" (nodes connecting different areas)
        - "Authorities" (nodes frequently referenced)
        - "Peripheral" (important nodes with few connections)
     3. Hypotheses about the reasons for the high centrality of certain nodes
     4. Possible gaps in the graph where centrality is unexpectedly low
     
     Present the result in a structured format with sections for each analysis category.
     ```

2. **Обнаружение и анализ сообществ**
   - Применение алгоритма Лувена или других методов обнаружения сообществ
   - Вычисление модулярности и других метрик качества разбиения

   - **Промпт для LLM (RU):**
     ```
     Проанализируйте следующие сообщества, выявленные в графе знаний для предметной области "{domain_type}".
     
     Данные по сообществам:
     {список сообществ с входящими узлами и внутренними/внешними связями}
     
     Для каждого сообщества определите:
     
     1. Тематическое ядро (основная концепция или тема, объединяющая узлы)
     2. Ключевые узлы внутри сообщества (по внутренней центральности)
     3. Граничные узлы (имеющие больше всего связей с другими сообществами)
     4. Отношения с другими сообществами (сильные/слабые, типы связей)
     5. Семантическую когерентность (насколько узлы действительно логически связаны)
     
     Кроме того, оцените общую структуру сообществ:
     - Являются ли выявленные сообщества естественными или искусственными
     - Есть ли "изолированные" сообщества, нуждающиеся в дополнительных связях
     - Присутствуют ли сообщества, которые логично было бы разделить дальше
     
     Представьте результат в структурированном формате с разделами для каждого сообщества и общих выводов.
     ```

   - **Промпт для LLM (EN):**
     ```
     Analyze the following communities detected in the knowledge graph for the domain "{domain_type}".
     
     Community data:
     {list of communities with included nodes and internal/external connections}
     
     For each community, determine:
     
     1. Thematic core (main concept or theme uniting the nodes)
     2. Key nodes within the community (by internal centrality)
     3. Boundary nodes (having the most connections with other communities)
     4. Relationships with other communities (strong/weak, types of connections)
     5. Semantic coherence (how logically connected the nodes actually are)
     
     Additionally, evaluate the overall community structure:
     - Whether the identified communities are natural or artificial
     - If there are "isolated" communities needing additional connections
     - Whether there are communities that would logically be further divided
     
     Present the result in a structured format with sections for each community and general conclusions.
     ```

3. **Анализ путей и структурных паттернов**
   - Вычисление всех кратчайших путей между ключевыми узлами
   - Обнаружение часто встречающихся подграфов и мотивов

   - **Промпт для LLM (RU):**
     ```
     Проанализируйте следующие пути и структурные паттерны в графе знаний для предметной области "{domain_type}".
     
     Кратчайшие пути между ключевыми узлами:
     {список кратчайших путей с задействованными узлами и рёбрами}
     
     Часто встречающиеся мотивы и подграфы:
     {список обнаруженных мотивов с частотой встречаемости}
     
     На основе этих данных определите:
     
     1. Логические цепочки рассуждений, представленные кратчайшими путями
     2. Повторяющиеся паттерны отношений и их интерпретация в контексте домена
     3. "Длинные" пути, которые могли бы быть сокращены (пропущенные прямые связи)
     4. Структурные особенности графа (иерархический, звездообразный, сетчатый и т.д.)
     5. Возможные "скрытые" отношения, не представленные явно, но следующие из структуры
     
     Представьте результат в структурированном формате с разделами для каждой категории анализа.
     ```

   - **Промпт для LLM (EN):**
     ```
     Analyze the following paths and structural patterns in the knowledge graph for the domain "{domain_type}".
     
     Shortest paths between key nodes:
     {list of shortest paths with involved nodes and edges}
     
     Frequently occurring motifs and subgraphs:
     {list of detected motifs with frequency of occurrence}
     
     Based on this data, determine:
     
     1. Logical chains of reasoning represented by the shortest paths
     2. Recurring relationship patterns and their interpretation in the domain context
     3. "Long" paths that could be shortened (missing direct connections)
     4. Structural features of the graph (hierarchical, star-shaped, mesh, etc.)
     5. Possible "hidden" relationships not explicitly represented but following from the structure
     
     Present the result in a structured format with sections for each analysis category.
     ```

4. **Определение стратегии дальнейшего исследования**
   - **Промпт для LLM (RU):**
     ```
     На основе проведенного структурного анализа графа знаний для предметной области "{domain_type}", сформулируйте стратегию дальнейшего исследования.
     
     Результаты анализа центральности:
     {резюме анализа центральности}
     
     Результаты анализа сообществ:
     {резюме анализа сообществ}
     
     Результаты анализа путей и паттернов:
     {резюме анализа путей и паттернов}
     
     Определите:
     
     1. Топ-5 приоритетных направлений для углубленного исследования:
        - Области с высокой центральностью, но недостаточной детализацией
        - "Мостовые" узлы, требующие уточнения
        - Потенциально пропущенные связи между сообществами
        - Неявные закономерности, требующие проверки
        - Структурные аномалии, требующие объяснения
     
     2. Для каждого направления сформулируйте:
        - Конкретные исследовательские вопросы
        - Гипотезы, которые следует проверить
        - Методы проверки (анализ текста, вопросы к LLM, структурный анализ)
        - Ожидаемый результат и его влияние на граф
     
     3. Предложите баланс между:
        - Расширением графа (добавление новых узлов и связей)
        - Углублением (детализация существующих узлов и связей)
        - Консолидацией (объединение дублирующих или схожих элементов)
        - Абстрагированием (формирование метаузлов и обобщений)
     
     Представьте результат в виде структурированного плана исследования.
     ```

   - **Промпт для LLM (EN):**
     ```
     Based on the structural analysis of the knowledge graph for the domain "{domain_type}", formulate a strategy for further research.
     
     Centrality analysis results:
     {summary of centrality analysis}
     
     Community analysis results:
     {summary of community analysis}
     
     Path and pattern analysis results:
     {summary of path and pattern analysis}
     
     Determine:
     
     1. Top 5 priority directions for in-depth research:
        - Areas with high centrality but insufficient detail
        - "Bridge" nodes requiring clarification
        - Potentially missed connections between communities
        - Implicit patterns requiring verification
        - Structural anomalies requiring explanation
     
     2. For each direction, formulate:
        - Specific research questions
        - Hypotheses to be tested
        - Verification methods (text analysis, questions to LLM, structural analysis)
        - Expected result and its impact on the graph
     
     3. Suggest a balance between:
        - Graph expansion (adding new nodes and connections)
        - Deepening (detailing existing nodes and connections)
        - Consolidation (merging duplicate or similar elements)
        - Abstraction (forming meta-nodes and generalizations)
     
     Present the result as a structured research plan.
     ```

### Инструменты:
- Библиотеки для анализа графов (NetworkX, graph-tool)
- Алгоритмы обнаружения сообществ (метод Лувена, InfoMap)
- Визуализаторы графов для наглядного представления (Gephi, Graphviz)
- LLM API (Claude 3.7 Sonnet)

### Обработка ошибок:
- **Проблема: Слишком большой граф для эффективного вычисления всех метрик**
  - Решение: Выборочное вычисление для ключевых узлов, определенных по базовым метрикам
  - Резервный метод: Использование приближенных алгоритмов для крупных графов

- **Проблема: Неинформативное разбиение на сообщества**
  - Решение: Поэкспериментировать с различными алгоритмами и параметрами разбиения
  - Резервный метод: Ручное определение ключевых тематических кластеров на основе семантики

- **Проблема: LLM предоставляет слишком общие или противоречивые рекомендации**
  - Решение: Итеративное уточнение с более конкретными вопросами
  - Резервный метод: Автоматическое формирование исследовательских вопросов на основе структурных метрик

### Выход:
Детальный анализ структуры графа с идентификацией ключевых узлов, сообществ и паттернов, а также конкретный план дальнейшего исследования.

## IV. Рекурсивное расширение и уточнение графа

### Цель:
Итеративно расширить и уточнить граф знаний, фокусируясь на выявленных приоритетных направлениях исследования.

### Алгоритм:
1. **Формулирование исследовательских вопросов**
   - **Промпт для LLM (RU):**
     ```
     На основе следующей информации о приоритетном направлении исследования в графе знаний для предметной области "{domain_type}":
     
     Направление: {описание направления из стратегии}
     Текущие узлы и связи: {подграф, относящийся к данному направлению}
     
     Сформулируйте 3-5 конкретных исследовательских вопросов, которые:
     
     1. Направлены на заполнение выявленных пробелов в знаниях
     2. Проверяют неявные гипотезы, следующие из структуры графа
     3. Уточняют отношения между ключевыми концепциями
     4. Исследуют потенциальные противоречия
     5. Фокусируются на "мостовых" узлах или границах между сообществами
     
     Для каждого вопроса укажите:
     - Конкретную формулировку вопроса
     - Какие узлы и связи затрагивает вопрос
     - Тип ожидаемого ответа (новый узел, новая связь, уточнение атрибута и т.д.)
     - Почему этот вопрос является приоритетным
     
     Учитывайте контекстуальную информацию из исходного текста.
     Сформулируйте вопросы так, чтобы они были конкретными, но открытыми для исследования.
     
     Представьте результат в структурированном формате с отдельным разделом для каждого вопроса.
     ```

   - **Промпт для LLM (EN):**
     ```
     Based on the following information about a priority research direction in the knowledge graph for the domain "{domain_type}":
     
     Direction: {description of the direction from the strategy}
     Current nodes and connections: {subgraph related to this direction}
     
     Formulate 3-5 specific research questions that:
     
     1. Aim to fill identified knowledge gaps
     2. Test implicit hypotheses following from the graph structure
     3. Clarify relationships between key concepts
     4. Explore potential contradictions
     5. Focus on "bridge" nodes or boundaries between communities
     
     For each question, specify:
     - Specific question formulation
     - Which nodes and connections the question affects
     - Type of expected answer (new node, new connection, attribute clarification, etc.)
     - Why this question is a priority
     
     Consider contextual information from the original text.
     Formulate questions so that they are specific but open for research.
     
     Present the result in a structured format with a separate section for each question.
     ```

2. **Генерация развёрнутых рассуждений по вопросам**
   - **Промпт для LLM (RU):**
     ```
     <|thinking|>
     Исследовательский вопрос: {конкретный исследовательский вопрос}
     
     Контекст вопроса:
     {описание затрагиваемого подграфа и исходных текстовых фрагментов}
     
     Подробно исследуйте этот вопрос, используя следующий структурированный подход:
     
     1. Анализ исходных данных:
        - Что мы уже знаем из имеющегося графа и текста?
        - Какие неявные предположения содержатся в этих данных?
        - Какие ключевые термины и концепции требуют уточнения?
     
     2. Разработка гипотез:
        - Сформулируйте несколько альтернативных гипотез
        - Оцените сильные и слабые стороны каждой гипотезы
        - Выделите наиболее правдоподобную гипотезу с обоснованием
     
     3. Логические выводы:
        - Какие новые концепции следуют из выбранной гипотезы?
        - Какие отношения между существующими концепциями уточняются?
        - Какие потенциальные противоречия возникают и как их можно разрешить?
     
     4. Междисциплинарные связи:
        - Как данный вопрос связан с другими областями знаний?
        - Какие аналогии или метафоры могут быть полезны для понимания?
        - Какие специфичные для домена закономерности проявляются?
     
     5. Синтез новых знаний:
        - Какие новые сущности и отношения следует добавить в граф?
        - Как уточнить существующие сущности и отношения?
        - Какие метаконцепции или обобщения можно сформулировать?
     
     В своих рассуждениях стремитесь к глубине и оригинальности, но сохраняйте логическую строгость и связь с исходными данными.
     <|/thinking|>
     ```

   - **Промпт для LLM (EN):**
     ```
     <|thinking|>
     Research question: {specific research question}
     
     Question context:
     {description of the affected subgraph and original text fragments}
     
     Explore this question in detail using the following structured approach:
     
     1. Analysis of initial data:
        - What do we already know from the existing graph and text?
        - What implicit assumptions are contained in this data?
        - Which key terms and concepts require clarification?
     
     2. Hypothesis development:
        - Formulate several alternative hypotheses
        - Evaluate the strengths and weaknesses of each hypothesis
        - Highlight the most plausible hypothesis with justification
     
     3. Logical conclusions:
        - What new concepts follow from the chosen hypothesis?
        - What relationships between existing concepts are clarified?
        - What potential contradictions arise and how can they be resolved?
     
     4. Interdisciplinary connections:
        - How is this question related to other knowledge domains?
        - What analogies or metaphors may be useful for understanding?
        - What domain-specific patterns are manifesting?
     
     5. Synthesis of new knowledge:
        - What new entities and relationships should be added to the graph?
        - How to refine existing entities and relationships?
        - What meta-concepts or generalizations can be formulated?
     
     In your reasoning, strive for depth and originality, but maintain logical rigor and connection to the source data.
     <|/thinking|>
     ```

3. **Извлечение новых знаний из рассуждений**
   - **Промпт для LLM (RU):**
     ```
     Проанализируйте следующее рассуждение по исследовательскому вопросу и выделите структурированные знания для дополнения графа.
     
     Исследовательский вопрос: {исследовательский вопрос}
     
     Рассуждение:
     {текст развёрнутого рассуждения}
     
     Выделите:
     
     1. Новые сущности, которые следует добавить в граф:
        - Название
        - Тип
        - Атрибуты
        - Источник в рассуждении (цитата)
        - Уверенность (0-1)
     
     2. Новые отношения между сущностями:
        - Исходная сущность
        - Целевая сущность
        - Тип отношения
        - Направление
        - Источник в рассуждении (цитата)
        - Уверенность (0-1)
     
     3. Уточнения существующих сущностей:
        - Сущность
        - Атрибут для уточнения
        - Новое значение
        - Источник в рассуждении (цитата)
        - Уверенность (0-1)
     
     4. Уточнения существующих отношений:
        - Отношение (исходная и целевая сущности)
        - Аспект для уточнения (тип, сила, направление)
        - Новое значение
        - Источник в рассуждении (цитата)
        - Уверенность (0-1)
     
     5. Метаконцепции или обобщения:
        - Название
        - Описание
        - Связанные сущности
        - Источник в рассуждении (цитата)
        - Уверенность (0-1)
     
     Представьте результат в JSON-формате с разделами для каждой категории.
     Фокусируйтесь на существенных дополнениях и изменениях, игнорируя тривиальные.
     ```

   - **Промпт для LLM (EN):**
     ```
     Analyze the following reasoning on a research question and extract structured knowledge to supplement the graph.
     
     Research question: {research question}
     
     Reasoning:
     {text of detailed reasoning}
     
     Extract:
     
     1. New entities to add to the graph:
        - Name
        - Type
        - Attributes
        - Source in reasoning (quote)
        - Confidence (0-1)
     
     2. New relationships between entities:
        - Source entity
        - Target entity
        - Relationship type
        - Direction
        - Source in reasoning (quote)
        - Confidence (0-1)
     
     3. Clarifications of existing entities:
        - Entity
        - Attribute to clarify
        - New value
        - Source in reasoning (quote)
        - Confidence (0-1)
     
     4. Clarifications of existing relationships:
        - Relationship (source and target entities)
        - Aspect to clarify (type, strength, direction)
        - New value
        - Source in reasoning (quote)
        - Confidence (0-1)
     
     5. Meta-concepts or generalizations:
        - Name
        - Description
        - Related entities
        - Source in reasoning (quote)
        - Confidence (0-1)
     
     Present the result in JSON format with sections for each category.
     Focus on substantial additions and changes, ignoring trivial ones.
     ```

4. **Интеграция новых знаний в граф**
   - **Промпт для LLM (RU):**
     ```
     Проверьте следующие предлагаемые дополнения к графу знаний на согласованность с существующей структурой.
     
     Существующий фрагмент графа:
     {релевантный подграф, который будет изменен}
     
     Предлагаемые дополнения:
     {JSON с новыми сущностями, отношениями и уточнениями}
     
     Для каждого предлагаемого дополнения проверьте:
     
     1. Согласованность с существующими знаниями:
        - Не противоречит ли новая информация существующей?
        - Не дублирует ли она уже имеющуюся информацию?
        - Соответствует ли она общей структуре и терминологии графа?
     
     2. Логическая целостность:
        - Не создает ли новая информация циклические зависимости?
        - Не нарушает ли она доменные ограничения или правила?
        - Корректны ли типы сущностей и отношений?
     
     3. Релевантность и полезность:
        - Насколько дополнение существенно для понимания домена?
        - Заполняет ли оно важный пробел в знаниях?
        - Улучшает ли оно связность графа?
     
     Для каждого дополнения укажите:
     - Статус (принять/отклонить/модифицировать)
     - Обоснование решения
     - Предлагаемые модификации (если необходимо)
     
     Представьте результат в структурированном формате с разделами для каждого дополнения.
     ```

   - **Промпт для LLM (EN):**
     ```
     Check the following proposed additions to the knowledge graph for consistency with the existing structure.
     
     Existing graph fragment:
     {relevant subgraph that will be modified}
     
     Proposed additions:
     {JSON with new entities, relationships, and clarifications}
     
     For each proposed addition, check:
     
     1. Consistency with existing knowledge:
        - Does the new information contradict existing information?
        - Does it duplicate already available information?
        - Does it match the general structure and terminology of the graph?
     
     2. Logical integrity:
        - Does the new information create cyclic dependencies?
        - Does it violate domain constraints or rules?
        - Are the entity and relationship types correct?
     
     3. Relevance and usefulness:
        - How significant is the addition for understanding the domain?
        - Does it fill an important knowledge gap?
        - Does it improve graph connectivity?
     
     For each addition, specify:
     - Status (accept/reject/modify)
     - Justification for the decision
     - Proposed modifications (if necessary)
     
     Present the result in a structured format with sections for each addition.
     ```

5. **Оценка прогресса и итеративное продолжение**
   - **Промпт для LLM (RU):**
     ```
     Оцените прогресс исследования после последнего цикла расширения графа знаний для предметной области "{domain_type}".
     
     Начальное состояние графа:
     {метрики графа до расширения}
     
     Текущее состояние графа:
     {метрики графа после расширения}
     
     Добавленные элементы:
     {список новых сущностей и отношений}
     
     Проанализируйте:
     
     1. Количественный прогресс:
        - Процент роста графа (по узлам и рёбрам)
        - Изменение ключевых метрик (центральность, модулярность, кластеризация)
        - Насколько заполнены выявленные ранее пробелы
     
     2. Качественный прогресс:
        - Появление новых значимых концепций
        - Уточнение существующих важных отношений
        - Возникновение новых структурных паттернов
     
     3. Направление дальнейшего исследования:
        - Какие вопросы остаются открытыми
        - Какие новые направления исследования появились
        - Какие аспекты требуют глубокой консолидации или абстрагирования
     
     4. Решение о дальнейших действиях:
        - Продолжать расширение (в каких направлениях)
        - Переходить к консолидации и абстрагированию
        - Фокусироваться на выявлении противоречий и их разрешении
     
     Представьте результат в структурированном формате с разделами для каждой категории анализа.
     ```

   - **Промпт для LLM (EN):**
     ```
     Evaluate the research progress after the last cycle of knowledge graph expansion for the domain "{domain_type}".
     
     Initial graph state:
     {graph metrics before expansion}
     
     Current graph state:
     {graph metrics after expansion}
     
     Added elements:
     {list of new entities and relationships}
     
     Analyze:
     
     1. Quantitative progress:
        - Percentage of graph growth (by nodes and edges)
        - Changes in key metrics (centrality, modularity, clustering)
        - How much previously identified gaps have been filled
     
     2. Qualitative progress:
        - Emergence of new significant concepts
        - Clarification of existing important relationships
        - Emergence of new structural patterns
     
     3. Direction of further research:
        - Which questions remain open
        - What new research directions have emerged
        - Which aspects require deep consolidation or abstraction
     
     4. Decision on further actions:
        - Continue expansion (in which directions)
        - Move to consolidation and abstraction
        - Focus on identifying contradictions and resolving them
     
     Present the result in a structured format with sections for each analysis category.
     ```

### Инструменты:
- LLM API (Claude 3.7 Sonnet)
- Библиотеки для работы с графами и их визуализации
- Система отслеживания изменений графа
- Хранилище промежуточных результатов

### Обработка ошибок:
- **Проблема: LLM генерирует рассуждения, слабо связанные с исходным вопросом**
  - Решение: Повторная отправка вопроса с более конкретными ограничениями и контекстом
  - Резервный метод: Разбиение сложного вопроса на серию более простых

- **Проблема: Предлагаемые дополнения противоречат существующему графу**
  - Решение: Автоматическое выявление противоречий и отправка LLM запроса на их разрешение
  - Резервный метод: Сохранение альтернативных версий графа с разными интерпретациями

- **Проблема: Циклическое повторение одних и тех же вопросов или идей**
  - Решение: Отслеживание истории вопросов и принудительное изменение фокуса
  - Резервный метод: Временное "замораживание" части графа и фокусировка на других областях

### Выход:
Расширенный и уточненный граф знаний с новыми сущностями, отношениями и метаконцепциями, а также решение о переходе к следующему этапу (продолжение расширения или переход к абстрагированию).

## V. Абстрагирование и создание метаграфа

### Цель:
Выявить более высокоуровневые структуры и обобщения в графе знаний, создав метаграф с абстрактными концепциями и отношениями.

### Алгоритм:
1. **Выявление кластеров для абстрагирования**
   - На основе структурного анализа (сообщества, k-core и т.д.)
   - С учетом семантической близости узлов

   - **Промпт для LLM (RU):**
     ```
     Проанализируйте следующие кластеры узлов в графе знаний для предметной области "{domain_type}" и определите, какие из них подходят для абстрагирования в метаконцепции.
     
     Кластеры узлов:
     {список кластеров с входящими узлами и их атрибутами}
     
     Для каждого кластера оцените:
     
     1. Семантическая согласованность (0-10):
        - Насколько узлы действительно связаны по смыслу
        - Есть ли общая тема или принцип, объединяющий узлы
        - Насколько узлы принадлежат к одному уровню абстракции
     
     2. Структурная целостность (0-10):
        - Насколько кластер изолирован от других кластеров
        - Насколько плотно связаны узлы внутри кластера
        - Наличие центрального узла или группы узлов
     
     3. Потенциал абстрагирования (0-10):
        - Возможность сформулировать единую метаконцепцию
        - Полезность абстракции для понимания домена
        - Возможность упрощения графа без потери существенной информации
     
     4. Предлагаемое название метаконцепции:
        - Короткое, но информативное название
        - Отражающее суть объединяемых концепций
        - Соответствующее терминологии домена
     
     Для кластеров с общим показателем (сумма всех оценок) выше 20, предложите краткое определение метаконцепции и основные атрибуты, которые она должна сохранить.
     
     Представьте результат в структурированном формате с разделами для каждого кластера.
     ```

   - **Промпт для LLM (EN):**
     ```
     Analyze the following node clusters in the knowledge graph for the domain "{domain_type}" and determine which ones are suitable for abstraction into meta-concepts.
     
     Node clusters:
     {list of clusters with included nodes and their attributes}
     
     For each cluster, evaluate:
     
     1. Semantic coherence (0-10):
        - How meaningfully the nodes are actually connected
        - Whether there is a common theme or principle uniting the nodes
        - How much the nodes belong to the same level of abstraction
     
     2. Structural integrity (0-10):
        - How isolated the cluster is from other clusters
        - How densely connected the nodes are within the cluster
        - Presence of a central node or group of nodes
     
     3. Abstraction potential (0-10):
        - Possibility to formulate a unified meta-concept
        - Usefulness of abstraction for understanding the domain
        - Possibility to simplify the graph without losing essential information
     
     4. Proposed meta-concept name:
        - Short but informative name
        - Reflecting the essence of the unified concepts
        - Corresponding to domain terminology
     
     For clusters with a total score (sum of all assessments) above 20, suggest a brief definition of the meta-concept and the main attributes it should retain.
     
     Present the result in a structured format with sections for each cluster.
     ```

2. **Формирование метаконцепций**
   - **Промпт для LLM (RU):**
     ```
     На основе следующего кластера узлов из графа знаний для предметной области "{domain_type}", сформулируйте метаконцепцию, которая объединяет и абстрагирует эти узлы.
     
     Кластер: {название кластера}
     Узлы кластера:
     {список узлов с атрибутами и отношениями}
     
     Внутренние связи:
     {список отношений между узлами внутри кластера}
     
     Внешние связи:
     {список отношений между узлами кластера и внешними узлами}
     
     Сформулируйте:
     
     1. Название метаконцепции:
        - Точное и информативное
        - Отражающее суть объединяемых концепций
        - В соответствии с терминологией домена
     
     2. Определение метаконцепции:
        - Чёткое и краткое определение (1-2 предложения)
        - Охватывающее все ключевые аспекты входящих узлов
        - На правильном уровне абстракции
     
     3. Ключевые атрибуты:
        - Общие атрибуты, которые сохраняются из исходных узлов
        - Новые атрибуты, возникающие на уровне метаконцепции
        - Вариативные атрибуты, отражающие разнообразие входящих узлов
     
     4. Внутренняя структура:
        - Как входящие узлы относятся друг к другу внутри метаконцепции
        - Какие подкатегории можно выделить
        - Какая иерархия или типология может быть применена
     
     5. Отношения с другими концепциями:
        - Как метаконцепция соотносится с другими частями графа
        - Какие типы отношений сохраняются на мета-уровне
        - Какие новые типы отношений возникают
     
     Обеспечьте баланс между абстрактностью (для объединения разнородных элементов) и конкретностью (для сохранения существенной информации).
     Представьте результат в структурированном формате с разделами для каждого аспекта метаконцепции.
     ```

   - **Промпт для LLM (EN):**
     ```
     Based on the following cluster of nodes from the knowledge graph for the domain "{domain_type}", formulate a meta-concept that unifies and abstracts these nodes.
     
     Cluster: {cluster name}
     Cluster nodes:
     {list of nodes with attributes and relationships}
     
     Internal connections:
     {list of relationships between nodes within the cluster}
     
     External connections:
     {list of relationships between cluster nodes and external nodes}
     
     Formulate:
     
     1. Meta-concept name:
        - Precise and informative
        - Reflecting the essence of the unified concepts
        - In accordance with domain terminology
     
     2. Meta-concept definition:
        - Clear and concise definition (1-2 sentences)
        - Covering all key aspects of the included nodes
        - At the right level of abstraction
     
     3. Key attributes:
        - Common attributes preserved from the original nodes
        - New attributes emerging at the meta-concept level
        - Variable attributes reflecting the diversity of included nodes
     
     4. Internal structure:
        - How the included nodes relate to each other within the meta-concept
        - What subcategories can be identified
        - What hierarchy or typology can be applied
     
     5. Relationships with other concepts:
        - How the meta-concept relates to other parts of the graph
        - What types of relationships are preserved at the meta-level
        - What new types of relationships emerge
     
     Ensure a balance between abstraction (to unify diverse elements) and concreteness (to preserve essential information).
     Present the result in a structured format with sections for each aspect of the meta-concept.
     ```

3. **Определение отношений между метаконцепциями**
   - **Промпт для LLM (RU):**
     ```
     Проанализируйте отношения между следующими метаконцепциями, сформированными из графа знаний для предметной области "{domain_type}".
     
     Метаконцепция A: {название и определение метаконцепции A}
     Исходные узлы: {список узлов, вошедших в метаконцепцию A}
     
     Метаконцепция B: {название и определение метаконцепции B}
     Исходные узлы: {список узлов, вошедших в метаконцепцию B}
     
     Существующие отношения между узлами:
     {список отношений между узлами метаконцепции A и метаконцепции B}
     
     На основе этих данных:
     
     1. Определите, существует ли значимое мета-отношение между концепциями:
        - Оцените силу связи на основе количества и типов существующих отношений
        - Определите, является ли связь фундаментальной или случайной
        - Укажите уверенность в наличии мета-отношения (0-1)
     
     2. Если мета-отношение существует, сформулируйте:
        - Тип мета-отношения (например, "причина-следствие", "часть-целое", "абстракция-конкретизация")
        - Направление (от A к B, от B к A, двунаправленное)
        - Краткое описание сути отношения (1-2 предложения)
     
     3. Проанализируйте семантическое содержание:
        - Какие аспекты метаконцепций связаны отношением
        - Какая информация теряется при абстрагировании отношения
        - Какие новые аспекты отношения видны только на уровне мета-концепций
     
     4. Предложите формализацию:
        - Как обозначить это отношение в метаграфе
        - Какие атрибуты должно иметь это отношение
        - Как количественно измерить силу этого отношения
     
     Представьте результат в структурированном формате с разделами для каждого аспекта анализа.
     ```

   - **Промпт для LLM (EN):**
     ```
     Analyze the relationships between the following meta-concepts formed from the knowledge graph for the domain "{domain_type}".
     
     Meta-concept A: {name and definition of meta-concept A}
     Original nodes: {list of nodes included in meta-concept A}
     
     Meta-concept B: {name and definition of meta-concept B}
     Original nodes: {list of nodes included in meta-concept B}
     
     Existing relationships between nodes:
     {list of relationships between nodes of meta-concept A and meta-concept B}
     
     Based on this data:
     
     1. Determine if a significant meta-relationship exists between the concepts:
        - Evaluate the strength of the connection based on the number and types of existing relationships
        - Determine if the connection is fundamental or coincidental
        - Indicate confidence in the presence of a meta-relationship (0-1)
     
     2. If a meta-relationship exists, formulate:
        - Type of meta-relationship (e.g., "cause-effect", "part-whole", "abstraction-concretization")
        - Direction (from A to B, from B to A, bidirectional)
        - Brief description of the essence of the relationship (1-2 sentences)
     
     3. Analyze the semantic content:
        - Which aspects of the meta-concepts are connected by the relationship
        - What information is lost when abstracting the relationship
        - What new aspects of the relationship are visible only at the meta-concept level
     
     4. Suggest formalization:
        - How to denote this relationship in the meta-graph
        - What attributes this relationship should have
        - How to quantitatively measure the strength of this relationship
     
     Present the result in a structured format with sections for each aspect of the analysis.
     ```

4. **Создание и верификация метаграфа**
   - **Промпт для LLM (RU):**
     ```
     Проверьте следующий метаграф на логическую согласованность и информативность для предметной области "{domain_type}".
     
     Метаконцепции:
     {список метаконцепций с определениями и атрибутами}
     
     Мета-отношения:
     {список мета-отношений между метаконцепциями}
     
     Проанализируйте:
     
     1. Структурную согласованность:
        - Все ли метаконцепции связаны (нет изолированных узлов)
        - Сбалансирована ли структура (нет доминирования одной метаконцепции)
        - Нет ли циклических зависимостей, которые могут указывать на логические ошибки
     
     2. Семантическую согласованность:
        - Корректность отношений между метаконцепциями
        - Соответствие определений метаконцепций их положению в графе
        - Отсутствие противоречий в атрибутах и отношениях
     
     3. Информативность:
        - Насколько метаграф отражает ключевые аспекты домена
        - Достаточен ли уровень абстракции для понимания общей картины
        - Сохранены ли существенные детали из исходного графа
     
     4. Полезность для дальнейшего анализа:
        - Какие выводы можно сделать из структуры метаграфа
        - Какие закономерности или паттерны становятся видны
        - Какие гипотезы можно сформулировать на основе метаграфа
     
     Для каждого выявленного недостатка предложите конкретное решение (добавление/удаление/изменение метаконцепций или отношений).
     
     Представьте результат в структурированном формате с разделами для каждого аспекта анализа.
     ```

   - **Промпт для LLM (EN):**
     ```
     Check the following meta-graph for logical consistency and informativeness for the domain "{domain_type}".
     
     Meta-concepts:
     {list of meta-concepts with definitions and attributes}
     
     Meta-relationships:
     {list of meta-relationships between meta-concepts}
     
     Analyze:
     
     1. Structural consistency:
        - Are all meta-concepts connected (no isolated nodes)
        - Is the structure balanced (no dominance of one meta-concept)
        - Are there any cyclic dependencies that might indicate logical errors
     
     2. Semantic consistency:
        - Correctness of relationships between meta-concepts
        - Correspondence of meta-concept definitions to their position in the graph
        - Absence of contradictions in attributes and relationships
     
     3. Informativeness:
        - How well the meta-graph reflects key aspects of the domain
        - Whether the level of abstraction is sufficient for understanding the big picture
        - Whether essential details from the original graph are preserved
     
     4. Usefulness for further analysis:
        - What conclusions can be drawn from the meta-graph structure
        - What patterns or regularities become visible
        - What hypotheses can be formulated based on the meta-graph
     
     For each identified shortcoming, suggest a specific solution (adding/removing/changing meta-concepts or relationships).
     
     Present the result in a structured format with sections for each aspect of the analysis.
     ```

5. **Связывание метаграфа с исходным графом**
   - **Промпт для LLM (RU):**
     ```
     Создайте би-направленные связи между метаграфом и исходным графом знаний для предметной области "{domain_type}".
     
     Метаконцепции:
     {список метаконцепций с определениями}
     
     Исходные узлы для каждой метаконцепции:
     {для каждой метаконцепции - список входящих в неё узлов}
     
     Для каждой метаконцепции:
     
     1. Типизируйте входящие узлы:
        - Ключевые узлы (наиболее репрезентативные для метаконцепции)
        - Поддерживающие узлы (хорошо соответствующие, но не определяющие)
        - Пограничные узлы (частично соответствующие или спорные)
     
     2. Определите отношения между метаконцепцией и исходными узлами:
        - Тип отношения (например, "является экземпляром", "иллюстрирует", "частичное соответствие")
        - Сила связи (0-1)
        - Объяснение, какие аспекты узла соответствуют метаконцепции
     
     3. Идентифицируйте контрпримеры:
        - Узлы, которые могли бы входить в метаконцепцию, но были исключены
        - Причины исключения
        - Пограничные случаи, требующие дополнительного анализа
     
     4. Создайте навигационные подсказки:
        - Как метаконцепция помогает понять структуру связанных узлов
        - Какие аспекты исходных узлов лучше видны через призму метаконцепции
        - Какие исследовательские вопросы можно задать на уровне метаконцепции
     
     Представьте результат в структурированном формате с разделами для каждой метаконцепции.
     ```

   - **Промпт для LLM (EN):**
     ```
     Create bi-directional links between the meta-graph and the original knowledge graph for the domain "{domain_type}".
     
     Meta-concepts:
     {list of meta-concepts with definitions}
     
     Original nodes for each meta-concept:
     {for each meta-concept - a list of nodes included in it}
     
     For each meta-concept:
     
     1. Categorize the included nodes:
        - Key nodes (most representative for the meta-concept)
        - Supporting nodes (well-corresponding but not defining)
        - Boundary nodes (partially corresponding or controversial)
     
     2. Define relationships between the meta-concept and original nodes:
        - Relationship type (e.g., "is an instance of", "illustrates", "partial correspondence")
        - Connection strength (0-1)
        - Explanation of which aspects of the node correspond to the meta-concept
     
     3. Identify counterexamples:
        - Nodes that could belong to the meta-concept but were excluded
        - Reasons for exclusion
        - Borderline cases requiring additional analysis
     
     4. Create navigation hints:
        - How the meta-concept helps understand the structure of related nodes
        - Which aspects of the original nodes are better seen through the lens of the meta-concept
        - What research questions can be asked at the meta-concept level
     
     Present the result in a structured format with sections for each meta-concept.
     ```

### Инструменты:
- Алгоритмы кластеризации графов
- LLM API (Claude 3.7 Sonnet)
- Визуализаторы для метаграфов
- Система для би-направленного связывания исходного графа и метаграфа

### Обработка ошибок:
- **Проблема: Слишком гетерогенные кластеры, не поддающиеся абстрагированию**
  - Решение: Рекурсивное разбиение кластеров на подкластеры
  - Резервный метод: Использование alternative clustering методов с разными критериями

- **Проблема: Метаконцепции слишком абстрактные или слишком конкретные**
  - Решение: Итеративное уточнение уровня абстракции с обратной связью
  - Резервный метод: Создание многоуровневой иерархии абстракции

- **Проблема: Потеря важной информации при абстрагировании**
  - Решение: Сохранение аннотаций с важными деталями при создании метаконцепций
  - Резервный метод: Двунаправленное отслеживание связей между исходными узлами и метаузлами

### Выход:
Метаграф с абстрактными концепциями и отношениями, связанный с исходным графом, предоставляющий более высокоуровневый взгляд на предметную область.

## VI. Формулирование теорий и гипотез

### Цель:
На основе графа знаний и метаграфа сформулировать целостные теории, объясняющие структуру предметной области, и выдвинуть проверяемые гипотезы.

### Алгоритм:
1. **Выявление закономерностей и паттернов**
   - **Промпт для LLM (RU):**
     ```
     Проанализируйте следующие структурные и семантические особенности графа знаний и метаграфа для предметной области "{domain_type}" и выявите закономерности и паттерны.
     
     Структурные особенности графа:
     {метрики графа, ключевые узлы, сообщества, пути}
     
     Метаграф:
     {метаконцепции и отношения между ними}
     
     Выявите следующие типы закономерностей:
     
     1. Структурные паттерны:
        - Иерархические структуры (древовидные отношения)
        - Циклические структуры (взаимозависимости)
        - Звездообразные структуры (центральные концепции)
        - Пересекающиеся сообщества (мультидисциплинарные области)
     
     2. Причинно-следственные цепочки:
        - Последовательности отношений типа "причина-следствие"
        - Каскадные эффекты (один узел влияет на многие)
        - Конвергентные причины (многие узлы влияют на один)
     
     3. Часто встречающиеся мотивы:
        - Повторяющиеся триады или более сложные структуры
        - Характерные паттерны связей между определенными типами узлов
        - Инвариантные отношения в разных частях графа
     
     4. Аномалии и особые случаи:
        - Необычные отклонения от общих закономерностей
        - Противоречивые или парадоксальные отношения
        - Изолированные структуры, не соответствующие общей картине
     
     Для каждой выявленной закономерности укажите:
     - Четкое описание паттерна
     - Где в графе он проявляется (конкретные узлы или подграфы)
     - Возможная интерпретация в контексте домена
     - Насколько закономерность универсальна для данного графа (локальная или глобальная)
     
     Сконцентрируйтесь на содержательных и неочевидных закономерностях, а не на тривиальных.
     Представьте результат в структурированном формате с разделами для каждого типа закономерностей.
     ```

   - **Промпт для LLM (EN):**
     ```
     Analyze the following structural and semantic features of the knowledge graph and meta-graph for the domain "{domain_type}" and identify patterns and regularities.
     
     Structural features of the graph:
     {graph metrics, key nodes, communities, paths}
     
     Meta-graph:
     {meta-concepts and relationships between them}
     
     Identify the following types of patterns:
     
     1. Structural patterns:
        - Hierarchical structures (tree-like relationships)
        - Cyclic structures (interdependencies)
        - Star-shaped structures (central concepts)
        - Overlapping communities (multidisciplinary areas)
     
     2. Cause-effect chains:
        - Sequences of "cause-effect" type relationships
        - Cascade effects (one node affects many)
        - Convergent causes (many nodes affect one)
     
     3. Frequently occurring motifs:
        - Repeating triads or more complex structures
        - Characteristic connection patterns between certain types of nodes
        - Invariant relationships in different parts of the graph
     
     4. Anomalies and special cases:
        - Unusual deviations from general patterns
        - Contradictory or paradoxical relationships
        - Isolated structures that do not correspond to the general picture
     
     For each identified pattern, specify:
     - Clear description of the pattern
     - Where in the graph it manifests (specific nodes or subgraphs)
     - Possible interpretation in the domain context
     - How universal the pattern is for this graph (local or global)
     
     Focus on meaningful and non-obvious patterns, not trivial ones.
     Present the result in a structured format with sections for each type of pattern.
     ```

2. **Формулирование теорий**
   - **Промпт для LLM (RU):**
     ```
     На основе выявленных закономерностей и паттернов в графе знаний для предметной области "{domain_type}", сформулируйте целостную теорию, которая объясняет структуру и отношения в данной области.
     
     Выявленные закономерности и паттерны:
     {список закономерностей с описаниями}
     
     Ключевые метаконцепции:
     {список основных метаконцепций}
     
     Сформулируйте теорию, включающую:
     
     1. Название теории:
        - Краткое и точное
        - Отражающее суть объяснения
        - В соответствии с терминологией домена
     
     2. Основные постулаты:
        - 3-5 ключевых утверждений, на которых основана теория
        - Каждый постулат должен быть четким и проверяемым
        - Постулаты должны быть логически связаны между собой
     
     3. Объяснительный механизм:
        - Как теория объясняет выявленные закономерности
        - Причинно-следственные или структурные механизмы
        - Уровни или иерархия объяснения
     
     4. Область применимости:
        - К каким частям графа теория применима полностью
        - Где есть ограничения или исключения
        - Условия, при которых теория действует
     
     5. Предсказательная сила:
        - Какие новые закономерности можно предсказать на основе теории
        - Какие потенциальные узлы или связи могут существовать, но не отражены в графе
        - Какие изменения могут произойти при определенных условиях
     
     6. Связь с существующими теориями:
        - Как данная теория соотносится с известными концепциями в этой области
        - Что нового она добавляет к существующему пониманию
        - Где она уточняет или противоречит устоявшимся взглядам
     
     Стремитесь к теории, которая:
     - Проста (использует минимум необходимых понятий)
     - Полна (объясняет большинство выявленных закономерностей)
     - Фальсифицируема (может быть опровергнута конкретными наблюдениями)
     - Генеративна (позволяет делать новые предсказания)
     
     Представьте теорию в структурированном формате с разделами для каждого аспекта.
     ```

   - **Промпт для LLM (EN):**
     ```
     Based on the identified patterns and regularities in the knowledge graph for the domain "{domain_type}", formulate a comprehensive theory that explains the structure and relationships in this field.
     
     Identified patterns and regularities:
     {list of patterns with descriptions}
     
     Key meta-concepts:
     {list of main meta-concepts}
     
     Formulate a theory including:
     
     1. Theory name:
        - Brief and precise
        - Reflecting the essence of the explanation
        - In accordance with domain terminology
     
     2. Basic postulates:
        - 3-5 key statements on which the theory is based
        - Each postulate should be clear and verifiable
        - Postulates should be logically connected to each other
     
     3. Explanatory mechanism:
        - How the theory explains the identified patterns
        - Causal or structural mechanisms
        - Levels or hierarchy of explanation
     
     4. Scope of applicability:
        - To which parts of the graph the theory is fully applicable
        - Where there are limitations or exceptions
        - Conditions under which the theory operates
     
     5. Predictive power:
        - What new patterns can be predicted based on the theory
        - What potential nodes or connections may exist but are not reflected in the graph
        - What changes may occur under certain conditions
     
     6. Relationship with existing theories:
        - How this theory relates to known concepts in the field
        - What new insights it adds to existing understanding
        - Where it refines or contradicts established views
     
     Strive for a theory that is:
     - Simple (uses the minimum necessary concepts)
     - Complete (explains most of the identified patterns)
     - Falsifiable (can be disproven by specific observations)
     - Generative (allows for new predictions)
     
     Present the theory in a structured format with sections for each aspect.
     ```

3. **Выдвижение проверяемых гипотез**
   - **Промпт для LLM (RU):**
     ```
     На основе сформулированной теории для предметной области "{domain_type}", выдвиньте набор проверяемых гипотез.
     
     Теория:
     {текст теории с постулатами и механизмами}
     
     Сформулируйте 5-7 конкретных гипотез, которые:
     
     1. Каждая гипотеза должна:
        - Быть сформулирована в виде чёткого утверждения
        - Быть логически связана с теорией
        - Быть конкретной и проверяемой
        - Выходить за рамки уже известных фактов
     
     2. Для каждой гипотезы укажите:
        - Формулировка в формате "если..., то..."
        - Логическая связь с постулатами теории
        - Какие данные или наблюдения могут подтвердить гипотезу
        - Какие данные или наблюдения могут опровергнуть гипотезу
        - Возможный метод проверки в контексте имеющегося графа или дополнительных данных
     
     3. Включите гипотезы разных типов:
        - Предсказательные (о новых узлах или связях, которые должны существовать)
        - Объяснительные (о механизмах, лежащих в основе наблюдаемых паттернов)
        - Сравнительные (о различиях между разными частями графа)
        - Условные (о том, как изменения в одной части графа влияют на другие)
     
     4. Для каждой гипотезы оцените:
        - Степень новизны (насколько гипотеза выходит за рамки известного)
        - Потенциальное значение (что даст подтверждение или опровержение гипотезы)
        - Сложность проверки (насколько реалистично проверить гипотезу)
     
     Гипотезы должны быть разнообразными и охватывать различные аспекты теории.
     Выбирайте гипотезы, проверка которых может привести к значительному уточнению или расширению теории.
     
     Представьте результат в структурированном формате с отдельным разделом для каждой гипотезы.
     ```

   - **Промпт для LLM (EN):**
     ```
     Based on the formulated theory for the domain "{domain_type}", put forward a set of testable hypotheses.
     
     Theory:
     {theory text with postulates and mechanisms}
     
     Formulate 5-7 specific hypotheses that:
     
     1. Each hypothesis should:
        - Be formulated as a clear statement
        - Be logically connected to the theory
        - Be specific and testable
        - Go beyond already known facts
     
     2. For each hypothesis, specify:
        - Formulation in "if..., then..." format
        - Logical connection with the theory's postulates
        - What data or observations can confirm the hypothesis
        - What data or observations can refute the hypothesis
        - Possible testing method in the context of the existing graph or additional data
     
     3. Include hypotheses of different types:
        - Predictive (about new nodes or connections that should exist)
        - Explanatory (about mechanisms underlying observed patterns)
        - Comparative (about differences between different parts of the graph)
        - Conditional (about how changes in one part of the graph affect others)
     
     4. For each hypothesis, evaluate:
        - Degree of novelty (how much the hypothesis goes beyond what is known)
        - Potential significance (what confirmation or refutation of the hypothesis will provide)
        - Testing complexity (how realistic it is to test the hypothesis)
     
     Hypotheses should be diverse and cover various aspects of the theory.
     Choose hypotheses whose testing may lead to significant refinement or extension of the theory.
     
     Present the result in a structured format with a separate section for each hypothesis.
     ```

4. **Проверка гипотез на существующих данных**
   - **Промпт для LLM (RU):**
     ```
     Проверьте следующие гипотезы на основе существующего графа знаний для предметной области "{domain_type}".
     
     Гипотезы:
     {список гипотез с формулировками и методами проверки}
     
     Граф знаний:
     {структура графа, релевантная для проверки гипотез}
     
     Для каждой гипотезы:
     
     1. Проведите анализ имеющихся данных:
        - Какие узлы и связи в графе релевантны для проверки гипотезы
        - Существуют ли прямые свидетельства, подтверждающие или опровергающие гипотезу
        - Какие косвенные свидетельства могут быть релевантны
     
     2. Проведите структурный анализ:
        - Соответствует ли структура графа тому, что предсказывает гипотеза
        - Существуют ли аномалии или исключения
        - Насколько сильны статистические закономерности, если они релевантны
     
     3. Сделайте вывод о статусе гипотезы:
        - Подтверждена (сильные прямые свидетельства)
        - Частично подтверждена (косвенные или ограниченные свидетельства)
        - Не подтверждена (нет релевантных свидетельств)
        - Опровергнута (свидетельства противоречат гипотезе)
        - Требует дополнительных данных (существующих данных недостаточно)
     
     4. Предложите уточнения:
        - Как гипотеза может быть модифицирована в свете полученных результатов
        - Какие дополнительные условия или ограничения следует учесть
        - Какие новые гипотезы могут возникнуть из текущих результатов
     
     Представьте результат в структурированном формате с разделами для каждой гипотезы.
     ```

   - **Промпт для LLM (EN):**
     ```
     Test the following hypotheses based on the existing knowledge graph for the domain "{domain_type}".
     
     Hypotheses:
     {list of hypotheses with formulations and testing methods}
     
     Knowledge graph:
     {graph structure relevant to testing hypotheses}
     
     For each hypothesis:
     
     1. Analyze available data:
        - Which nodes and connections in the graph are relevant for testing the hypothesis
        - Whether there is direct evidence confirming or refuting the hypothesis
        - What indirect evidence may be relevant
     
     2. Conduct structural analysis:
        - Whether the graph structure corresponds to what the hypothesis predicts
        - Whether there are anomalies or exceptions
        - How strong are statistical patterns, if relevant
     
     3. Conclude on the hypothesis status:
        - Confirmed (strong direct evidence)
        - Partially confirmed (indirect or limited evidence)
        - Not confirmed (no relevant evidence)
        - Refuted (evidence contradicts the hypothesis)
        - Requires additional data (existing data is insufficient)
     
     4. Suggest refinements:
        - How the hypothesis can be modified in light of the results
        - What additional conditions or limitations should be considered
        - What new hypotheses may arise from current results
     
     Present the result in a structured format with sections for each hypothesis.
     ```

5. **Уточнение теорий на основе проверки гипотез**
   - **Промпт для LLM (RU):**
     ```
     На основе результатов проверки гипотез уточните теорию для предметной области "{domain_type}".
     
     Исходная теория:
     {текст исходной теории с постулатами и механизмами}
     
     Результаты проверки гипотез:
     {результаты для каждой гипотезы: статус и выводы}
     
     Сформулируйте уточнённую теорию, которая:
     
     1. Учитывает результаты проверки:
        - Включает подтверждённые аспекты исходной теории
        - Модифицирует или удаляет опровергнутые аспекты
        - Уточняет области неопределённости
     
     2. Содержит обновлённые постулаты:
        - Укажите, какие постулаты остаются неизменными
        - Какие модифицируются (с объяснением изменений)
        - Какие новые постулаты добавляются (с обоснованием)
     
     3. Уточняет объяснительный механизм:
        - Как изменилось понимание причинно-следственных связей
        - Какие новые факторы или условия были выявлены
        - Как изменилась структурная модель объяснения
     
     4. Переопределяет область применимости:
        - Где теория применима с высокой уверенностью
        - Где есть ограничения или исключения
        - Какие новые условия применимости были выявлены
     
     5. Оценивает общие изменения:
        - Насколько существенно изменилась теория
        - Какие ключевые инсайты были получены
        - Как изменилась общая парадигма понимания домена
     
     Представьте уточнённую теорию в структурированном формате, ясно показывая изменения относительно исходной версии.
     Выделите ключевые отличия и объясните их теоретическое и практическое значение.
     ```

   - **Промпт для LLM (EN):**
     ```
     Based on the results of hypothesis testing, refine the theory for the domain "{domain_type}".
     
     Original theory:
     {text of the original theory with postulates and mechanisms}
     
     Hypothesis testing results:
     {results for each hypothesis: status and conclusions}
     
     Formulate a refined theory that:
     
     1. Takes into account testing results:
        - Includes confirmed aspects of the original theory
        - Modifies or removes refuted aspects
        - Clarifies areas of uncertainty
     
     2. Contains updated postulates:
        - Indicate which postulates remain unchanged
        - Which are modified (with explanation of changes)
        - What new postulates are added (with justification)
     
     3. Refines the explanatory mechanism:
        - How the understanding of cause-effect relationships has changed
        - What new factors or conditions have been identified
        - How the structural model of explanation has changed
     
     4. Redefines the scope of applicability:
        - Where the theory is applicable with high confidence
        - Where there are limitations or exceptions
        - What new conditions of applicability have been identified
     
     5. Evaluates overall changes:
        - How substantially the theory has changed
        - What key insights were gained
        - How the general paradigm of domain understanding has changed
     
     Present the refined theory in a structured format, clearly showing changes relative to the original version.
     Highlight key differences and explain their theoretical and practical significance.
     ```

### Инструменты:
- LLM API (Claude 3.7 Sonnet)
- Алгоритмы для обнаружения и анализа паттернов в графах
- Система для отслеживания связей между теориями, гипотезами и данными
- Визуализация для наглядного представления теорий

### Обработка ошибок:
- **Проблема: LLM формулирует слишком общие или тривиальные теории**
  - Решение: Дополнительные промпты с просьбой о конкретизации и глубине
  - Резервный метод: Генерация нескольких альтернативных теорий и их сравнение

- **Проблема: Гипотезы не поддаются проверке на имеющихся данных**
  - Решение: Формулирование альтернативных гипотез или модификация существующих
  - Резервный метод: Явное указание на необходимость дополнительных данных

- **Проблема: Противоречия между разными теориями или гипотезами**
  - Решение: Специальные промпты для анализа противоречий и поиска синтеза
  - Резервный метод: Сохранение альтернативных теорий с указанием их преимуществ и ограничений

### Выход:
Набор структурированных теорий с уточненными постулатами, объяснительными механизмами и областями применимости, а также проверенные (или требующие дальнейшей проверки) гипотезы.

## VII. Генерация итоговых результатов

### Цель:
Синтезировать и представить результаты анализа в формате, соответствующем потребностям пользователя и специфике предметной области.

### Алгоритм:
1. **Определение оптимального формата представления**
   - **Промпт для LLM (RU):**
     ```
     На основе исходной задачи пользователя и предметной области "{domain_type}", определите оптимальный формат представления результатов анализа.
     
     Исходная задача пользователя:
     {описание задачи из предварительного опроса}
     
     Тип входных данных:
     {тип текста - научные статьи, интервью, художественное произведение и т.д.}
     
     Основные результаты анализа:
     {краткое резюме основных теорий, гипотез и выявленных паттернов}
     
     Определите:
     
     1. Основной формат представления:
        - Научный отчёт (для академических или исследовательских целей)
        - Аналитическая справка (для бизнес-решений или стратегического планирования)
        - Герменевтическая интерпретация (для литературного анализа)
        - Дискурсивный анализ (для исследования социальных или коммуникативных явлений)
        - Решение расследования (для детективных или юридических случаев)
        - Другое (опишите)
     
     2. Структура основного документа:
        - Какие разделы должны быть включены
        - Какая информация должна быть в каждом разделе
        - Логическая последовательность изложения
        - Необходимый уровень детализации
     
     3. Дополнительные материалы:
        - Визуализации (какие типы будут наиболее информативны)
        - Таблицы и схемы (какие данные следует структурировать)
        - Примеры и извлечения из исходного текста (как их лучше интегрировать)
        - Ссылки на исходные фрагменты (как их организовать)
     
     4. Стиль и язык:
        - Формальность (научный, деловой, популярный)
        - Техничность (насколько использовать специализированную терминологию)
        - Целевая аудитория (эксперты, широкая публика, смешанная)
        - Тон и подача (нейтральный, убеждающий, исследовательский)
     
     Представьте результат в виде детального плана документа с обоснованием выбора формата и структуры.
     ```

   - **Промпт для LLM (EN):**
     ```
     Based on the user's original task and the domain "{domain_type}", determine the optimal format for presenting the analysis results.
     
     User's original task:
     {task description from the preliminary survey}
     
     Input data type:
     {text type - scientific articles, interviews, literary work, etc.}
     
     Main analysis results:
     {brief summary of main theories, hypotheses, and identified patterns}
     
     Determine:
     
     1. Main presentation format:
        - Scientific report (for academic or research purposes)
        - Analytical brief (for business decisions or strategic planning)
        - Hermeneutic interpretation (for literary analysis)
        - Discourse analysis (for studying social or communicative phenomena)
        - Investigation solution (for detective or legal cases)
        - Other (describe)
     
     2. Main document structure:
        - What sections should be included
        - What information should be in each section
        - Logical sequence of presentation
        - Required level of detail
     
     3. Additional materials:
        - Visualizations (which types will be most informative)
        - Tables and diagrams (what data should be structured)
        - Examples and extracts from the source text (how to best integrate them)
        - References to original fragments (how to organize them)
     
     4. Style and language:
        - Formality (scientific, business, popular)
        - Technicality (how much to use specialized terminology)
        - Target audience (experts, general public, mixed)
        - Tone and delivery (neutral, persuasive, exploratory)
     
     Present the result as a detailed document plan with justification for the choice of format and structure.
     ```

2. **Генерация основного документа**
   - **Промпт для LLM (RU):**
     ```
     Создайте итоговый аналитический документ для предметной области "{domain_type}" в соответствии с определённым форматом и структурой.
     
     Формат документа:
     {определённый формат и структура}
     
     Основные результаты анализа:
     {теории, гипотезы, паттерны и другие ключевые находки}
     
     Граф знаний:
     {ключевые узлы, связи и структурные особенности графа}
     
     Метаграф:
     {основные метаконцепции и их взаимосвязи}
     
     Создайте документ, который:
     
     1. Следует указанной структуре и формату
     2. Интегрирует все ключевые результаты анализа
     3. Использует соответствующий стиль и язык
     4. Включает ссылки на исходные данные там, где это необходимо
     5. Представляет информацию в логической последовательности
     6. Соблюдает баланс между глубиной и доступностью
     
     Документ должен быть целостным, связным и информативным, представляя результаты анализа в наиболее эффективной форме.
     
     Включите в документ:
     - Резюме/аннотацию (если применимо)
     - Все необходимые разделы согласно структуре
     - Логические переходы между разделами
     - Заключительные выводы или рекомендации
     
     Оптимизируйте изложение для максимального понимания целевой аудиторией.
     ```

   - **Промпт для LLM (EN):**
     ```
     Create a final analytical document for the domain "{domain_type}" in accordance with the defined format and structure.
     
     Document format:
     {defined format and structure}
     
     Main analysis results:
     {theories, hypotheses, patterns, and other key findings}
     
     Knowledge graph:
     {key nodes, connections, and structural features of the graph}
     
     Meta-graph:
     {main meta-concepts and their interrelationships}
     
     Create a document that:
     
     1. Follows the specified structure and format
     2. Integrates all key analysis results
     3. Uses appropriate style and language
     4. Includes references to source data where necessary
     5. Presents information in a logical sequence
     6. Maintains a balance between depth and accessibility
     
     The document should be cohesive, coherent, and informative, presenting the analysis results in the most effective form.
     
     Include in the document:
     - Summary/abstract (if applicable)
     - All necessary sections according to the structure
     - Logical transitions between sections
     - Final conclusions or recommendations
     
     Optimize the presentation for maximum understanding by the target audience.
     ```

3. **Создание визуализаций и дополнительных материалов**
   - **Промпт для LLM (RU):**
     ```
     Опишите необходимые визуализации и дополнительные материалы для представления результатов анализа предметной области "{domain_type}".
     
     Основные результаты анализа:
     {ключевые теории, гипотезы и паттерны}
     
     Структура графа знаний:
     {ключевые узлы, сообщества и структурные особенности}
     
     Определите набор визуализаций и дополнительных материалов, включая:
     
     1. Графовые визуализации:
        - Какие подграфы следует визуализировать
        - Какие метрики использовать для размера, цвета, формы узлов
        - Какие типы рёбер выделить визуально
        - Какой уровень детализации предпочтителен
     
     2. Концептуальные диаграммы:
        - Диаграммы, отображающие метаконцепции и их отношения
        - Иерархические структуры или таксономии
        - Причинно-следственные диаграммы
        - Концептуальные карты для ключевых теорий
     
     3. Таблицы и структурированные данные:
        - Сравнительные таблицы для альтернативных теорий или интерпретаций
        - Матрицы отношений между ключевыми концепциями
        - Количественные данные, подтверждающие определённые закономерности
        - Списки ключевых узлов с их метриками и атрибутами
     
     4. Текстовые дополнения:
        - Глоссарий ключевых терминов
        - Примеры из исходного текста, иллюстрирующие выводы
        - Альтернативные интерпретации спорных моментов
        - FAQ по основным аспектам анализа
     
     Для каждой предложенной визуализации или материала укажите:
     - Конкретное содержание
     - Формат представления
     - Как материал дополняет основной документ
     - Техническую реализацию (если релевантно)
     
     Представьте результат в виде структурированного списка с детальным описанием каждого элемента.
     ```

   - **Промпт для LLM (EN):**
     ```
     Describe the necessary visualizations and additional materials for presenting the analysis results of the domain "{domain_type}".
     
     Main analysis results:
     {key theories, hypotheses, and patterns}
     
     Knowledge graph structure:
     {key nodes, communities, and structural features}
     
     Define a set of visualizations and additional materials, including:
     
     1. Graph visualizations:
        - Which subgraphs should be visualized
        - Which metrics to use for size, color, shape of nodes
        - Which types of edges to highlight visually
        - What level of detail is preferable
     
     2. Conceptual diagrams:
        - Diagrams showing meta-concepts and their relationships
        - Hierarchical structures or taxonomies
        - Cause-effect diagrams
        - Concept maps for key theories
     
     3. Tables and structured data:
        - Comparative tables for alternative theories or interpretations
        - Relationship matrices between key concepts
        - Quantitative data supporting certain patterns
        - Lists of key nodes with their metrics and attributes
     
     4. Textual supplements:
        - Glossary of key terms
        - Examples from the source text illustrating conclusions
        - Alternative interpretations of contentious issues
        - FAQ on main aspects of the analysis
     
     For each proposed visualization or material, specify:
     - Specific content
     - Presentation format
     - How the material complements the main document
     - Technical implementation (if relevant)
     
     Present the result as a structured list with a detailed description of each element.
     ```

4. **Самооценка и критическое рассмотрение**
   - **Промпт для LLM (RU):**
     ```
     Проведите критическую самооценку результатов анализа предметной области "{domain_type}".
     
     Основные результаты анализа:
     {ключевые теории, гипотезы и выводы}
     
     Методология анализа:
     {основные этапы и подходы, использованные в анализе}
     
     Оцените следующие аспекты:
     
     1. Полнота анализа:
        - Насколько полно охвачена предметная область
        - Какие аспекты могли быть упущены или недостаточно проработаны
        - Достаточно ли глубоко проанализированы ключевые концепции
     
     2. Надёжность выводов:
        - Насколько выводы подтверждены имеющимися данными
        - Где присутствует спекулятивность или недостаток обоснований
        - Насколько устойчивы выводы к альтернативным интерпретациям
     
     3. Методологические ограничения:
        - Какие ограничения есть у использованных методов
        - Как эти ограничения могли повлиять на результаты
        - Какие альтернативные методы могли бы дополнить анализ
     
     4. Потенциальные искажения:
        - Возможные систематические ошибки в анализе
        - Влияние предварительных гипотез на интерпретацию данных
        - Культурные, дисциплинарные или другие предубеждения
     
     5. Направления для дальнейшего исследования:
        - Ключевые открытые вопросы, требующие дополнительного изучения
        - Новые гипотезы, возникшие в процессе анализа
        - Потенциальные междисциплинарные связи для расширения анализа
     
     Представьте результат в структурированном формате с конкретными рекомендациями по укреплению надёжности анализа и дальнейшим исследованиям.
     Стремитесь к непредвзятой оценке, выделяя как сильные, так и слабые стороны проведённого анализа.
     ```

   - **Промпт для LLM (EN):**
     ```
     Conduct a critical self-assessment of the analysis results for the domain "{domain_type}".
     
     Main analysis results:
     {key theories, hypotheses, and conclusions}
     
     Analysis methodology:
     {main stages and approaches used in the analysis}
     
     Evaluate the following aspects:
     
     1. Comprehensiveness of analysis:
        - How completely the domain is covered
        - What aspects might have been missed or insufficiently elaborated
        - Whether key concepts are analyzed deeply enough
     
     2. Reliability of conclusions:
        - How well the conclusions are supported by available data
        - Where there is speculation or lack of justification
        - How robust the conclusions are to alternative interpretations
     
     3. Methodological limitations:
        - What limitations exist in the methods used
        - How these limitations might have affected the results
        - What alternative methods might have complemented the analysis
     
     4. Potential biases:
        - Possible systematic errors in the analysis
        - Influence of preliminary hypotheses on data interpretation
        - Cultural, disciplinary, or other biases
     
     5. Directions for further research:
        - Key open questions requiring additional study
        - New hypotheses that emerged during the analysis
        - Potential interdisciplinary connections to expand the analysis
     
     Present the result in a structured format with specific recommendations for strengthening the reliability of the analysis and further research.
     Strive for an unbiased assessment, highlighting both strengths and weaknesses of the conducted analysis.
     ```

### Инструменты:
- LLM API (Claude 3.7 Sonnet)
- Генераторы визуализаций для графов и диаграмм (Graphviz, D3.js)
- Инструменты для форматирования и структурирования документов
- Системы для создания итерактивных визуализаций (если требуется)

### Обработка ошибок:
- **Проблема: Документ слишком длинный или слишком краткий**
  - Решение: Уточнение параметров с конкретными требованиями по объему
  - Резервный метод: Многоуровневое представление с разной степенью детализации

- **Проблема: Недостаточная адаптация к предметной области**
  - Решение: Дополнительные промпты с примерами соответствующего формата
  - Резервный метод: Пост-обработка с учетом специфических требований области

- **Проблема: Техническая сложность визуализаций**
  - Решение: Создание упрощенных версий с сохранением ключевой информации
  - Резервный метод: Текстовое описание визуализаций для ручной реализации

### Выход:
Комплексный набор материалов, отражающих результаты анализа в формате, оптимизированном для задачи и предметной области, включая основной документ, визуализации и дополнительные материалы.

## VIII. Интеграция и контроль работы системы

### Цель:
Обеспечить эффективное функционирование всей системы, включая балансировку ресурсов, обработку ошибок и адаптацию к различным типам данных и задач.

### Алгоритм:
1. **Планирование последовательности операций**
   - Определение оптимальной последовательности этапов для конкретной задачи
   - Оценка ресурсоемкости каждого этапа и распределение ресурсов
   - Построение графика выполнения с контрольными точками

2. **Мониторинг и контроль качества**
   - Определение метрик качества для каждого этапа (например, согласованность графа, обоснованность теорий)
   - Регулярная оценка промежуточных результатов и коррекция процесса
   - Логирование всех действий и решений системы для последующего анализа

3. **Обработка ошибок и сбоев**
   - Детектирование проблем на каждом этапе (например, некорректный JSON-ответ от LLM)
   - Применение стратегий восстановления, описанных для каждого этапа
   - Адаптивная модификация промптов и параметров для улучшения результатов

4. **Оптимизация использования LLM API**
   - Кэширование результатов запросов для избежания дублирования
   - Группировка запросов для более эффективного использования контекстного окна
   - Динамическая регулировка частоты и сложности запросов

5. **Интерактивное взаимодействие с пользователем (опционально)**
   - Периодическое информирование о прогрессе анализа
   - Возможность вмешательства пользователя для корректировки направления исследования
   - Запрос уточнений при неоднозначных или критических решениях

6. **Постобработка и хранение результатов**
   - Оптимизация хранения промежуточных и финальных результатов
   - Индексация и поисковый доступ к полученным знаниям
   - Экспорт результатов в различные форматы для дальнейшего использования

### Технические аспекты:
1. **Архитектура системы**
   - Модульная структура с четко определенными интерфейсами между компонентами
   - Асинхронная обработка для параллельного выполнения независимых задач
   - Централизованное хранилище состояния с транзакционным доступом

2. **Управление ресурсами**
   - Динамическое выделение ресурсов в зависимости от сложности задачи
   - Приоритезация критических этапов анализа
   - Контроль использования API-квот и оптимизация расходов

3. **Обеспечение надежности**
   - Резервное копирование промежуточных результатов
   - Механизмы восстановления после сбоев
   - Изоляция ошибок для предотвращения каскадных сбоев

4. **Масштабирование**
   - Горизонтальное масштабирование для обработки больших корпусов текстов
   - Вертикальное масштабирование для глубокого анализа сложных концепций
   - Адаптивное распределение нагрузки на разные компоненты системы

### Инженерные решения:
1. **Базовая инфраструктура**
   - Контейнеризация (Docker) для обеспечения воспроизводимости и переносимости
   - Оркестрация (например, с помощью Kubernetes) для управления распределенной системой
   - Мониторинг (Prometheus, Grafana) для отслеживания производительности и ресурсов

2. **Хранение данных**
   - Графовая база данных (Neo4j) для хранения и запросов к графу знаний
   - Документоориентированная БД (MongoDB) для исходных и промежуточных данных
   - Векторное хранилище (Pinecone, Weaviate) для семантического поиска по контексту

3. **Интеграция с внешними сервисами**
   - Асинхронные клиенты для LLM API с управлением ошибками и повторными попытками
   - Кэширующий прокси для оптимизации запросов
   - Очереди сообщений (RabbitMQ, Kafka) для координации этапов обработки

4. **Пользовательский интерфейс (если требуется)**
   - Web-интерфейс для настройки параметров и мониторинга прогресса
   - API для интеграции с другими системами
   - Система визуализации для интерактивного исследования результатов

### Выход:
Интегрированная система, способная эффективно выполнять весь цикл анализа от обработки исходных текстов до генерации конечных результатов, с адаптивным управлением ресурсами и обработкой ошибок.

# Заключение

Предложенный план системы предоставляет подробное описание алгоритма для преобразования неструктурированных текстов в структурированные теории и знания через создание, расширение и анализ графа знаний. Система объединяет методы обработки естественного языка, анализа графов, машинного обучения и аргументации в единый процесс с четко определенными этапами, инструментами и стратегиями обработки ошибок.

Ключевые инновации подхода:
1. Контекстуальная сегментация с сохранением связей между фрагментами текста
2. Доменно-ориентированное извлечение сущностей и отношений
3. Рекурсивное расширение графа через генерацию исследовательских вопросов
4. Многоуровневое абстрагирование с созданием метаграфа
5. Формулирование и проверка теорий и гипотез
6. Адаптация выходных результатов к типу задачи и предметной области

Реализация системы требует интеграции различных компонентов и инструментов, включая LLM API, графовые базы данных, алгоритмы анализа графов и системы визуализации. Модульная архитектура обеспечивает гибкость и адаптивность к различным типам текстов и задач.

Такая система может найти применение в научных исследованиях, литературном анализе, UX-исследованиях, правовом и детективном анализе, и других областях, где требуется извлечение, структурирование и синтез знаний из текстовых данных.