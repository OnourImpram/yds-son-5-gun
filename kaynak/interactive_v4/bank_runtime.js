  function flattenExam(assessment) {
    return assessment.simulation.groups.flatMap(function(group){
      return group.questions.map(function(question){return Object.assign({_group:group},question);});
    });
  }
  const historicalQuestions = new Map(historical.diagnostic.concat(Object.values(historical.daily).flat(),flattenExam(historical)).map(function(q){return [q.id,q];}));
  function confidence(value) {
    return ['Düşük','Orta','Yüksek'].includes(value) ? value : '';
  }
  function validChoice(value, question) {
    return Number.isInteger(value) && value >= 0 && value < question.options.length;
  }
  function archive(records) {
    const byResponse = new Map();
    for (const record of (Array.isArray(records) ? records : [])) {
      if (!record || !historicalQuestions.has(record.id)) continue;
      const question = historicalQuestions.get(record.id);
      const selected = validChoice(record.choice, question) ? record.choice : null;
      const certainty = confidence(record.confidence);
      if (selected === null && !certainty) continue;
      const source = record.source === 'practice' ? 'practice' : 'book';
      const time = Number.isFinite(record.time) && record.time >= 0 ? record.time : 0;
      const key = JSON.stringify([record.id,selected,certainty,source,time]);
      byResponse.set(key,{id:record.id,choice:selected,confidence:certainty,source:source,time:time});
    }
    return Array.from(byResponse.values());
  }
  function migrateBook(raw) {
    const fields = Object.assign({},raw);
    const history = archive(fields.assessmentHistory);
    if (Number(fields.assessmentBank) !== 4) {
      for (const [id, order] of Object.entries(migration)) {
        const key = 'conf-'+id;
        const selected = typeof fields[id] === 'string' && /^[0-4]$/.test(fields[id]) ? Number(fields[id]) : null;
        if (order) {
          if (selected !== null) fields[id] = String(order[selected]);
        } else {
          history.push({id:id,choice:selected,confidence:fields[key],source:'book'});
          delete fields[id];
          delete fields[key];
        }
      }
    }
    fields.assessmentBank = 4;
    fields.assessmentHistory = archive(history);
    return fields;
  }
  window.YDSAssessmentBanks = {historical:historical,flattenExam:flattenExam,questions:historicalQuestions,
    migration:migration,archive:archive,migrateBook:migrateBook,confidence:confidence};
