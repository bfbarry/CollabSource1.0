import React, { useEffect, useState } from 'react';
import {useNavigate} from 'react-router-dom';
import { useAuthContext } from '../hooks/useAuthContext';
import {TextField, Autocomplete} from '@mui/material';
import '../index.css';

export default function CreateProject(props) {
  /* Form for creating project
  Renders different inputs depending on which project category is selected  */

  const {user} = useAuthContext();
  const [form, setForm] = useState([]);
  const [isLoaded, setIsLoaded] = useState(false);
  const [error, setError] = useState(null);
  const [output, setOutput] = useState({});
  const navigate = useNavigate();

  useEffect(() => {
    fetch(`/api/forms/create_project`)
    .then(res => res.json())
    .then(
      (data) => {
      setIsLoaded(true);
      setForm(data);
      },
      (error) => {
      setIsLoaded(true);
      setError(error);
      }
    )
    }, [])
  
  function handleChange(e) {
    /* setState function */
    const {name, value} = e.target;
    setOutput(prevOutput => ({
      ...prevOutput,
      [name]: value
    }))
  }
  
  async function submitHandler(e) {
    // post request
    e.preventDefault()
    try {
      let creators_arr = output.creators.split(',').map(el => el.trim());
      output.creators = creators_arr
      let tag_arr = output.tags.split(',').map(el => el.trim());
      output.tags = tag_arr; // BAD... but setOutput is literally not setting state?
      let wp_arr = output.wanted_positions.split(',').map(el => el.trim());
      output.wanted_positions = wp_arr; // BAD... but setOutput is literally not setting state?
    } catch (e) { } //do nothing 
    const opts = {
      method: 'POST',
      headers: new Headers({
        'Content-Type': 'application/json',
        "Authorization": `Bearer ${user.token}`
      }),
      body: JSON.stringify(output)
    }
    fetch('/api/project/create', opts)
      .then(res => {
        if (res.status === 200) return res.json()
        else return (<p>error</p>)
      })
      .then(data => {
        navigate(`/project/${data.id}`)
        })
      .catch(error => {
        console.error("error", error)
      } )
  }

  return ( //useref here?
    <div > 
    {/* onSubmit={submitHandler}  */}
      <div>
        <label htmlFor='name'> {form.name && form.name.label} </label> 
        <input type='text' 
              name='name'
              maxLength={form.name && form.name.maxlength}
              value={output.name || ''}
              onChange={handleChange}/> 
      </div>
      <div>
        <label htmlFor='category'> {form.category && form.category.label} </label>
        <select name='category'
              onChange={handleChange}
              value={output.category || ''}>
          {form.category && form.category.options.map(opt => (
            <option key={opt} > {opt} </option>
          ))}
        </select> 
      </div>
      <div> {/* Should have <i> hover that says that these people will be admins */}
        <label htmlFor='creators'> {form.creators && form.creators.label} </label> 
        <input type='text' 
              name='creators'
              value={output.creators || ''}
              onChange={handleChange}/> 
      </div>
      <div>
        <label htmlFor='descr'> {form.descr && form.descr.label} </label> 
        <textarea name='descr'
              maxLength={form.descr && form.descr.maxlength}
              value={output.descr || ''}
              onChange={handleChange}/> 
      </div>
      <div >
        <label > {form.skill_level && form.skill_level.label} </label>
        {form.skill_level && form.skill_level.options.map(lvl => (

            <label htmlFor='skill_level' key={lvl + 'label'} > 
              <input type='radio' 
                    key={lvl}
                    name='skill_level'
                    value={lvl || ''}
                    onChange={handleChange}/>
                 {lvl} &nbsp;
              </label>
        ))}
      </div>
      <div >
        <label > {form.setting && form.setting.label} </label>
        {form.setting && form.setting.options.map(stg => (

            <label htmlFor='setting' key={stg + 'label'} > 
              <input type='radio' 
                    key={stg}
                    name='setting'
                    value={stg || ''}
                    onChange={handleChange}/>
                 {stg} &nbsp;
              </label>
        ))}
      </div>
      <div >
        <label > {form.geo_type && form.geo_type.label} </label>
        {form.geo_type && form.geo_type.options.map(gt => (

            <label htmlFor='geo_type' key={gt + 'label'} > 
              <input type='radio' 
                    key={gt}
                    name='geo_type'
                    value={gt || ''}
                    onChange={handleChange}/>
                 {gt} &nbsp;
              </label>
        ))}
      </div>
      {output.geo_type === 'college/university' &&
        <Autocomplete
          id="college"
          options={form.college && form.college.options}
          getOptionLabel={(option) => option}
          style={{ width: 300 }}
          renderInput={(params) => <TextField {...params} 
            label="Enter and select college/university" 
            variant="outlined" 
            name='college'
            value={output.college || ''}
            onChange={handleChange}/>} // This no work
        />
      }
      

      {output.category === "learning" &&
        <div>
          <div>
            <label htmlFor='learning_category'> {form.learning_category && form.learning_category.label} </label>
            <select name='learning_category'
                  onChange={handleChange}
                  value={output.learning_category || ''}>
              {form.learning_category && form.learning_category.options.map(opt => (
                <option key={opt} > {opt} </option>
              ))}
            </select> 
          </div>
          <div>
            <label htmlFor='pace'> {form.pace && form.pace.label} </label>
            <select name='pace'
                  onChange={handleChange}
                  value={output.pace || ''}>
              {form.pace && form.pace.options.map(opt => (
                <option key={opt} > {opt} </option>
              ))}
            </select> 
          </div>
          <div>
            <label htmlFor='resource'> {form.resource && form.resource.label} </label> 
            <input type='text' 
                  name='resource'
                  maxLength={form.resource && form.resource.maxlength}
                  value={output.resource || ''}
                  onChange={handleChange}/> 
          </div>

        </div>
      }
      <div>
        <label htmlFor='tags'> Tags: </label> 
        <input type='text' 
              name='tags'
              value={output.tags || ''}
              onChange={handleChange}/> 
      </div>
      {/* Wanted positions */}
      <div>
        <label htmlFor='wanted_positions'> Wanted positions: </label> 
        <input type='text' 
              name='wanted_positions'
              value={output.wanted_positions || ''}
              onChange={handleChange}/> 
      </div>
    <button className='btn-lg btn-success' onClick={submitHandler}>Create Project!</button>
    </div>
  )
}

