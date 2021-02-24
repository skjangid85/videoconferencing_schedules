from enum import auto
from flask import Flask, render_template, request, redirect, url_for, flash
from flask.helpers import url_for
from flask_sqlalchemy import SQLAlchemy
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

app = Flask(__name__)
app.secret_key = "Secret Key"
app.config['SQLALCHEMY_DATABASE_URI']='postgresql://postgres:postgres@localhost/speed_collector'
db = SQLAlchemy(app)

class Data(db.Model):
    __tablename__='data'
    id=db.Column(db.Integer, primary_key=True)
    vc_date_=db.Column(db.Date)
    from_stn_=db.Column(db.String(120))
    to_stn_=db.Column(db.String(120))
    from_time_=db.Column(db.String(120))
    to_time_=db.Column(db.String(120))
    server_=db.Column(db.String(120))
    status_=db.Column(db.String(120))
    hours=db.Column(db.Integer)

    def __init__(self, vc_date_, from_stn_, to_stn_, from_time_, to_time_, server_, status_, hours):
        self.vc_date_ = vc_date_
        self.from_stn_ = from_stn_
        self.to_stn_ = to_stn_
        self.from_time_ = from_time_
        self.to_time_ = to_time_
        self.server_ = server_
        self.status_ = status_
        self.hours = hours


@app.route("/")
def index():
    all_data = Data.query.filter().order_by(Data.vc_date_.desc())
    return render_template("index.html", schedules = all_data)

@app.route("/filter/", methods = ['POST'])
def filter():
    if request.method == 'POST':
        fm_date = request.form['fm_date']
        to_date = request.form['to_date']
        all_data = Data.query.filter(Data.vc_date_.between(fm_date, to_date) ).order_by(Data.vc_date_.desc())
        return render_template("index.html", schedules = all_data)             
    else: 
        all_data = Data.query.filter().order_by(Data.vc_date_.desc())
        return render_template("index.html", schedules = all_data)
    # all_data = Data.query.all()    


@app.route("/cv/")
def cv():
    df = pd.read_sql_table('data', con=db.engine)
    df_fig = pd.DataFrame(df)

    df_avaya = df_fig[df_fig['server_'] == 'AVAYA']

    df_internet = df_fig[df_fig['server_'] == 'INTERNET']

    df_nextcloud = df_fig[df_fig['server_'] == 'Nextcloud']

    # Bar chart grouped
    fig = px.bar(df_fig, x="vc_date_", y='hours', color="server_", barmode="group")
    fig.update_layout(title='VC Conducted On All Servers', xaxis_title='Date',yaxis_title='Total Minutes')

    # Bar Grouped Chart
    fig2 = go.Figure(data=[go.Bar(name='AVAYA', x=df_avaya.vc_date_, y=df_avaya.hours),
    go.Bar(name='INTERNET', x=df_internet.vc_date_, y=df_internet.hours),
    go.Bar(name='Nextcloud', x=df_nextcloud.vc_date_, y=df_nextcloud.hours),
    ])
    fig2.update_layout(barmode='group')
    fig2.update_layout(xaxis_tickangle=-90)
    fig2.update_layout(title='VC Conducted On Our Servers', xaxis=dict(title='Date of VC', tickmode='linear'),
    yaxis_title='Total Minutes')

    # pie chart
    fig3 = px.pie(df_fig, values='hours', names='server_')
    fig3.update_layout(title='VC Conducted On All Servers Pie Chart')

    graph = fig.to_html(full_html=False, default_height=500, default_width=auto)
    graph2 = fig2.to_html(full_html=False, default_height=auto, default_width=auto)
    graph3 = fig3.to_html(full_html=False, default_height=auto, default_width=auto)
    return render_template("cv.html", graph = graph, graph2 = graph2, graph3 = graph3)


@app.route("/add_schedule/")
def add_schedule():
    return render_template("add_schedule.html")

@app.route("/projects/")
def projects():
    return render_template("projects-with-sidebar.html")

@app.route("/success", methods = ['POST'])
def success():
    if request.method == 'POST':
        vc_date = request.form['vc_date']
        from_stn = request.form['from_stn']
        to_stn = request.form['to_stn']
        from_time = request.form['from_time']
        to_time = request.form['to_time']
        server_type = request.form['server_type']
        status = request.form['status']
        fm_hr, fm_min = from_time.split(':')
        to_hr, to_min = to_time.split(':')
        minutes = abs(int(to_hr) - int(fm_hr)) * 60 + (int(to_min) - int(fm_min))

        my_data = Data(vc_date, from_stn, to_stn, from_time, to_time, server_type, status, minutes)
        db.session.add(my_data)
        db.session.commit() 

        flash("Vc Schedule Added Successfully!")
        return redirect(url_for('index'))

@app.route("/update", methods= ['GET', 'POST'])
def update():
    if request.method == 'POST':
        my_data = Data.query.get(request.form.get('id'))

        my_data.vc_date_ = request.form['vc_date']
        my_data.from_stn_ = request.form['from_stn']
        my_data.to_stn_ = request.form['to_stn']
        my_data.from_time_ = request.form['from_time']
        my_data.to_time_ = request.form['to_time']
        my_data.server_ = request.form['server_type']
        my_data.status_ = request.form['status']

        fm_hr, fm_min = request.form['from_time'].split(':')
        to_hr, to_min = request.form['to_time'].split(':')
        minutes = abs(int(to_hr) - int(fm_hr)) * 60 + (int(to_min) - int(fm_min))
        
        my_data.hours = minutes
        db.session.commit()
        flash("VC Schedule updated successfully")
        return redirect(url_for('index'))

@app.route("/delete/<id>/", methods=['GET','POST'])
def delete(id):
    my_data = Data.query.get(id)
    db.session.delete(my_data)
    db.session.commit()
    flash("Schedule Deleted Successfully")
    return redirect(url_for('index'))


if __name__ == "__main__":
    app.debug=True
    app.run()