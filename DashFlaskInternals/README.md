# Dash Application Debugging

----

### 02/05/24: Added `logging`, print statements & breakpoints

Focus is on ensuring that the application correctly handles user interactions without any logical errors, especially around the toggling of star ratings and the management of the `error_state`. 

The application should accurately update based on the selected filters and handle edge cases, such as no stars being selected (handled by `error_state`).

### Potential Issues/Concerns
- **Error Handling**: Ensuring that `error_state` is triggered and cleared correctly based on user actions.
- **Callback Dependencies**: Proper execution order and dependencies between callbacks might be causing unexpected behavior.
- **State Management**: Accurate tracking and updating of states (`selected-stars`, `error-state`, and `available-stars`) across callbacks.

----

### Problem toggling between departments containing 2/3 stars

Seems to break down in PACA with:

- Vaucluse, 
- Var, 
- Alpes Maritimes
- Bouches Rhone - (Also 3 star traces left over...)

----

### Breakpoints and Variables to Track

- **`update_button_active_state` Callback**:
  - **Breakpoints**:
    - At the beginning to inspect the initial states (`n_clicks_list`, `ids`, `current_stars`, `available_stars`).
    - Inside the loop where stars are added or removed.
    - Before returning the outputs to see the final states of `class_names`, `styles`, `new_stars`, and `error_state`.
  - **Variables**:
    - `n_clicks_list`, `ids`: To observe how each button is being interacted with.
    - `current_stars`, `new_stars`: To check which stars are active before and after processing.
    - `error_state`: To confirm if it's set/unset correctly based on the presence of active stars.
----
- **`update_sidebar` Callback**:
  - **Breakpoints**:
    - At the start to check incoming inputs (`clickData`, `selected_department`, `error_state`).
    - Before each return statement to inspect what is being output based on the conditions.
  - **Variables**:
    - `clickData`: To debug data received from map clicks.
    - `error_state`, `selected_department`: To understand how these influence the displayed content.
----
- **`update_map` Callback**:
  - **Breakpoints**:
    - At each condition check, especially where different plotting functions are called.
  - **Variables**:
    - `selected_department`, `selected_region`, `selected_stars`: To verify if the map is being updated according to these filters.
    - `error_state`: To ensure map updates are in line with the error conditions.

----

## Have thrown everything at it so far and ...

---


## Strategies to consider to manage execution of callbacks:

### 1. Prevent a callback from firing
- `PreventUpdate`: stop the callback from updating any outputs if certain conditions aren't met.

```python
from dash.exceptions import PreventUpdate

@app.callback(
    Output('output-component', 'property'),
    [Input('input-component', 'value')]
)
def update_output(value):
    if not value:  # Check for some condition
        raise PreventUpdate
    return f"Output updated to: {value}"
```

- `no_update`: selectively prevent updates for specific outputs while allowing others to proceed.

```python
from dash import no_update

@app.callback(
    [Output('output-1', 'property'), Output('output-2', 'property')],
    [Input('input-component', 'value')]
)
def update_multiple_outputs(value):
    if not value:
        return no_update, "Value is required for output 1"  # Only update output 2
    return f"Output 1 updated to: {value}", "Output 2 not required"

```

### 2. Use conditional callbacks
  - `dash.callback_context`: inspect which input triggered the callback, allowing you to implement logic that responds differently based on the source of the trigger.

```python
from dash import callback_context

@app.callback(
    Output('output-component', 'property'),
    [Input('input-1', 'value'), Input('input-2', 'value')]
)
def update_based_on_input(input1, input2):
    ctx = callback_context
    if not ctx.triggered:
        return "No input has been triggered yet."
    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]

    if trigger_id == 'input-1':
        return f"Input 1 triggered: {input1}"
    elif trigger_id == 'input-2':
        return f"Input 2 triggered: {input2}"
    return "Unexpected trigger"
```

### 3. Forcing Callback Execution
- Modify a hidden `dcc.Store` object (make an invisible component)
  - Change the state of a component (like a timestamp or a counter) that's used as an input to the callback. This can be useful to force a callback to re-run when other data changes indirectly affect the desired output. 

```python
@app.callback(
    Output('hidden-div', 'children'),  # Hidden div that doesn't affect layout
    [Input('trigger-button', 'n_clicks')]
)
def trigger_update(n_clicks):
    return str(datetime.now())  # Returning current timestamp to trigger other callbacks

@app.callback(
    Output('output-component', 'property'),
    [Input('hidden-div', 'children')]
)
def update_output(timestamp):
    # Update logic here that depends on other conditions, re-evaluated every time the timestamp updates
    return f"Updated at {timestamp}"
```

----

