import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error
from sklearn.model_selection import cross_val_score, train_test_split
from understat.analyse import get_team_history, get_teams_in_league


def correlation_test():
    """Correlating previous n weeks to n+1 week"""
    league = 'EPL'
    year = '2020'
    N = 3

    teams = get_teams_in_league(league, year)

    history = get_team_history(league, year, 0, teams)
    dim = history[0].shape

    # TODO: Put all in multi-level df
    pre_list = []
    res_list = []
    opp_list = []
    for team, games in zip(teams, history):
        for idx in range(0, dim[0] - N):

            stop = idx + N
            name = f"{team}{idx}"
            # Not actually numeric here as reading from csv, but pd.mean automatically converts objects to numeric types
            # and drops others
            pre = games.iloc[idx:stop]
            pre_series = pre.mean(numeric_only=True)
            pre_series.name = name
            pre_list.append(pre_series)

            # Selecting next game (looks same as last entry above, but remember : indexing is exclusive on RHS
            # Turning objects to numeric manually (Series function), setting errors to NaN and dropping
            next_game = games.iloc[stop]
            res_series = pd.to_numeric(next_game, errors='coerce').dropna()
            res_series.name = name
            res_list.append(res_series)

            opp_series = history[teams.index(next_game.opp)][idx:stop].mean(numeric_only=True)
            opp_series.name = name
            opp_list.append(opp_series)

    # Turning list of Series to df
    pre = pd.concat(pre_list, axis=1)
    res = pd.concat(res_list, axis=1)
    opp_pre = pd.concat(opp_list, axis=1)

    pre = pre.transpose().select_dtypes(include=[np.number])
    opp_pre = opp_pre.transpose().select_dtypes(include=[np.number])
    opp_pre = opp_pre.add_prefix("opp_")

    inp = pd.concat([pre, opp_pre], axis=1)
    inp.drop(columns=list(inp.filter(regex='npx')), inplace=True)
    out = res.loc["xG"]

    X_train, X_test, y_train, y_test = train_test_split(inp, out, test_size=0.2, random_state=0)

    lin_reg = LinearRegression()
    lin_reg.fit(X_train, y_train)

    y_pred = lin_reg.predict(X_test)
    mse = mean_squared_error(y_test, y_pred)
    rmse = np.sqrt(mse)

    cdf = pd.DataFrame(lin_reg.coef_, inp.columns, columns=['Coefficients'])
    cdf.sort_values('Coefficients', inplace=True, ascending=False, key=abs)
    scores = cross_val_score(lin_reg, inp, out,
                             scoring="neg_mean_squared_error", cv=10)
    cross_rmse = np.sqrt(-scores)

    # plt.subplots(2, 3)
    nPlot = 6
    names = cdf.index.values[:nPlot]
    fig, axs = plt.subplots(2, 3, constrained_layout=True)
    # fig.tight_layout()
    fig.suptitle(f"xG prediction by previous {N} games: Top {nPlot} correlations")
    for ax, name in zip(axs.ravel(), names):
        ax.set_title("corr = {0:.3f}".format(cdf.loc[name][0]))
        ax.scatter(X_test[name], y_test, color="black")
        ax.scatter(X_test[name], y_pred, color="blue")
        ax.set_xlabel(name)
        ax.set_ylabel("xG")

    # plt.xticks(())
    # plt.yticks(())
    plt.show()

    per_game = []
    for hist in history:
        per_game.append(hist.mean(numeric_only=True))

    per_game = pd.concat(per_game, axis=1)
    per_game.columns = teams
    return per_game


if __name__ == "__main__":

    correlation_test()
